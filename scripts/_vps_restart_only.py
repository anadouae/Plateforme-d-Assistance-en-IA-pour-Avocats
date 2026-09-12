#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
cmd = (
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart backend frontend celery-worker"
)
print(">>", cmd)
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
print("exit", o.channel.recv_exit_status())
_, o2, e2 = c.exec_command(
    "sleep 8 && curl -fsS -o /dev/null -w '%{http_code}' https://lexhub.space/",
    timeout=60,
)
print("http", o2.read().decode(errors="replace"), e2.read().decode(errors="replace"))
c.close()
