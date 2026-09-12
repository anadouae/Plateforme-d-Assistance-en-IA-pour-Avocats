#!/usr/bin/env python3
"""Deploy smart polish (gpt-4o) + action toasts."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
    "backend/app/services/billing.py",
    "frontend/src/store/action-toast.ts",
    "frontend/src/components/ui/action-toast-host.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -40",
    timeout=600,
)
print(o.read().decode(errors="replace")[-4500:])
err = e.read().decode(errors="replace")
if err:
    print("stderr:", err[-1500:])

# Smoke: confirm polish uses gpt-4o config
_, o2, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python -c \"from app.core.config import settings; "
    "print('OPENAI_MODEL', settings.OPENAI_MODEL); "
    "print('POLISH_LLM', settings.DICTATION_POLISH_USE_LLM)\"",
    timeout=60,
)
print(o2.read().decode(errors="replace"))
c.close()
print("done")
