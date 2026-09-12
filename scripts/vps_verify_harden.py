#!/usr/bin/env python3
import time
import urllib.request
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
t = c.get_transport()
if t:
    t.set_keepalive(15)

sftp = c.open_sftp()
sftp.put("docker-compose.lexhub.yml", f"{REMOTE}/docker-compose.lexhub.yml")
sftp.close()
print("compose uploaded")

# ensure frontend sees new compose mode
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"-f docker-compose.lexhub-fe-dev.yml up -d frontend 2>&1"
)
print(o.read().decode(errors="replace")[-800:])
c.close()

time.sleep(10)
for u in [
    "https://lexhub.space/api/health",
    "https://lexhub.space/mentions-legales",
    "https://lexhub.space/login",
]:
    try:
        r = urllib.request.urlopen(u, timeout=30)
        body = r.read(120)
        print(r.status, u, body[:100])
    except Exception as e:
        print("ERR", u, e)
