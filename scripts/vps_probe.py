#!/usr/bin/env python3
import time
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for i in range(8):
    try:
        c.connect(
            HOST,
            username="root",
            password=PASSWORD,
            timeout=60,
            banner_timeout=90,
            auth_timeout=60,
        )
        print("connected")
        break
    except Exception as e:
        print("retry", i, e)
        time.sleep(8)
else:
    raise SystemExit(1)

t = c.get_transport()
if t:
    t.set_keepalive(15)

_, o, e = c.exec_command(
    "uptime; docker ps -a --format '{{.Names}} {{.Status}}' | head -20; "
    "echo '---build log---'; tail -40 /tmp/sanad-fe-build.log 2>/dev/null || echo NOLOG; "
    "echo '---health---'; curl -sS http://127.0.0.1:8001/api/health | head -c 400"
)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print("ERR", err)
c.close()
