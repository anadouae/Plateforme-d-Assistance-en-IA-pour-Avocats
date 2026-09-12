#!/usr/bin/env python3
import time
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for i in range(6):
    try:
        c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
        break
    except Exception as e:
        print("retry", e)
        time.sleep(8)
else:
    raise SystemExit(1)

t = c.get_transport()
if t:
    t.set_keepalive(15)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("uploaded", rel)
sftp.close()
# next dev hot reload — soft restart frontend to be sure
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart frontend 2>&1"
)
print(o.read().decode(errors="replace"))
c.close()
print("done")
