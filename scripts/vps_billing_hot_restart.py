#!/usr/bin/env python3
"""Aggressive disk cleanup then hot-restart without full image rebuild if possible."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

# Prefer restart with mounted code over full rebuild
FILES = [
    "backend/alembic/versions/026_billing_subscriptions.py",
    "backend/app/models/__init__.py",
    "backend/app/core/config.py",
    "backend/app/main.py",
    "backend/app/api/auth.py",
    "backend/app/api/team.py",
    "backend/app/api/cases.py",
    "backend/app/api/dictation.py",
    "backend/app/api/billing.py",
    "backend/app/services/billing.py",
    "backend/app/services/pii_mask.py",
    "backend/app/services/cle_de_barre.py",
    "backend/app/services/free_llm_router.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/admin/plans/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-5000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

run(c, "df -h /")
# Keep named volumes (postgres/minio) — only prune unused images/containers/networks/build
run(c, "docker container prune -f; docker network prune -f; docker builder prune -af; docker image prune -af", timeout=400)
run(c, "journalctl --vacuum-size=50M 2>&1 | tail -3; rm -rf /var/tmp/* /tmp/npm* 2>/dev/null; df -h /")

sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP missing", rel)
        continue
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

# Check mounts
run(c, f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml config 2>/dev/null | grep -A2 'backend:' | head -5; docker inspect sanad-backend-1 --format '{{{{json .Mounts}}}}' 2>/dev/null | head -c 800; echo; docker ps --format '{{{{.Names}}}}'")

# Migration + recreate WITHOUT --build (use existing images + bind mounts)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -25",
    timeout=120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -30",
    timeout=300,
)
run(c, "sleep 10; curl -sS -o /dev/null -w 'tarifs=%{http_code}\\n' https://lexhub.space/tarifs; curl -sS -w '\\nplans=%{http_code}\\n' https://lexhub.space/api/billing/plans | tail -5")
c.close()
print("done")
