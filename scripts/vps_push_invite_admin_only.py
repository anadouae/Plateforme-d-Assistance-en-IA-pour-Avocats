#!/usr/bin/env python3
"""Deploy admin-only email invite flow (Option A)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/025_invite_role_name.py",
    "backend/app/api/team.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/join_code.py",
    "backend/app/services/email.py",
    "frontend/src/app/join/accept/page.tsx",
    "frontend/src/app/join/page.tsx",
    "frontend/src/components/auth/join-pipeline.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/lib/api.ts",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:200])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("stderr:", err[-1500:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -20",
    timeout=120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -25",
    timeout=600,
)
run(c, f"cd {REMOTE} && sleep 8 && curl -fsS -o /dev/null -w '%{{http_code}}' https://lexhub.space/login 2>&1")
c.close()
print("done")
