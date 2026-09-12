#!/usr/bin/env python3
"""Deploy batch UX: hero video, X fix, admin, hover nav, phone optional, etc."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/public/videos/hero-desk.mp4",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/app/admin/page.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/billing/smart-insights-strip.tsx",
    "frontend/src/lib/api.ts",
    "backend/app/schemas/__init__.py",
    "backend/app/api/auth.py",
    "backend/app/services/retention_lifecycle.py",
    "backend/app/services/plaidoirie_case_compose.py",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:200], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-3000:], flush=True)
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
    f"restart backend frontend 2>&1 | tail -25",
    180,
)
time.sleep(14)
run(c, "curl -sS -o /dev/null -w 'home=%{http_code}\\n' https://lexhub.space/", 40)
c.close()
print("DONE", flush=True)
