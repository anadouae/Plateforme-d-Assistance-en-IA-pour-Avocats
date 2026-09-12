#!/usr/bin/env python3
"""Deploy: Adminer, checkout auth, invite UX, density/RIB removal, IA compose, popups."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "docker-compose.lexhub.yml",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/app/join/accept/page.tsx",
    "frontend/src/app/activate/page.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/components/auth/auth-success-modal.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/settings/admin-cabinet-center.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/lib/api.ts",
    "backend/app/schemas/__init__.py",
    "backend/app/api/team.py",
    "backend/app/api/dictation.py",
    "backend/app/services/plaidoirie_case_compose.py",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:220], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-4000:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel, flush=True)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"--env-file .env.vps up -d adminer 2>&1 | tail -40",
    120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart backend frontend 2>&1 | tail -30",
    180,
)
time.sleep(16)
run(
    c,
    "curl -sS -o /dev/null -w 'home=%{http_code}\\n' https://lexhub.space/ && "
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python -c \"from app.core.config import settings; "
    "print('openai_key=' + ('yes' if bool(settings.OPENAI_API_KEY) else 'NO')); "
    "print('model=' + (settings.OPENAI_MODEL or '')); "
    "from app.services.free_llm_router import router_status; "
    "s=router_status(); print('openai_cfg', s.get('openai',{}).get('configured')); "
    "print('openai_avail', s.get('openai',{}).get('available'))\" 2>&1",
    60,
)
run(c, "ss -lntp | grep 8088 || true; docker ps --format '{{.Names}} {{.Status}}' | grep -E 'adminer|backend|frontend' || true", 30)
c.close()
print("DONE", flush=True)
