#!/usr/bin/env python3
import time
import paramiko

FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/api/dictation.py",
    "docker-compose.lexhub.yml",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
t = c.get_transport()
if t:
    t.set_keepalive(20)

sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

_, o, _ = c.exec_command(
    f"sed -i '/^DICTATION_LOCAL_ONLY=/d' {REMOTE}/.env; "
    f"echo 'DICTATION_LOCAL_ONLY=true' >> {REMOTE}/.env; "
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1"
)
print(o.read().decode(errors="replace")[-1800:])
time.sleep(6)
_, o2, _ = c.exec_command(
    "docker exec sanad-backend-1 printenv DICTATION_LOCAL_ONLY WHISPER_ENABLED WHISPER_MODEL"
)
print(o2.read().decode(errors="replace"))
c.close()
print("done")
