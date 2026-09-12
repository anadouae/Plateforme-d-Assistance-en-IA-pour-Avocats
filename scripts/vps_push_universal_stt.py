#!/usr/bin/env python3
import time
import paramiko

FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/api/dictation.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/api.ts",
]
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for i in range(8):
    try:
        c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
        break
    except Exception as e:
        print("retry", e)
        time.sleep(8)
else:
    raise SystemExit(1)

t = c.get_transport()
if t:
    t.set_keepalive(20)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1"
)
print(o.read().decode(errors="replace")[-2000:])
c.close()
print("done")
