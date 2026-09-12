#!/usr/bin/env python3
import paramiko

FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
    "frontend/src/lib/api.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 && "
    f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1"
)
print(o.read().decode(errors="replace")[-1200:])
c.close()
print("done")
