#!/usr/bin/env python3
"""Push fidélité dictée (texte = ce qui est dit, sans polish auto)."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/dictation.py",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("MISSING", rel)
        continue
    sftp.put(str(local), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 && "
    f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1",
    timeout=180,
)
print(o.read().decode(errors="replace")[-2500:])
print(e.read().decode(errors="replace")[-800:])
c.close()
print("done")
