#!/usr/bin/env python3
"""Deploy: delete pieces, polish LLM fix, revise chat, 80-char UX."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/dictation.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/schemas/__init__.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/api.ts",
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
    f"up -d --force-recreate backend frontend 2>&1 | tail -35",
    timeout=600,
)
print(o.read().decode(errors="replace")[-4000:])
err = e.read().decode(errors="replace")
if err:
    print("stderr:", err[-1500:])
c.close()
print("done")
