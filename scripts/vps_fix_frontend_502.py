#!/usr/bin/env python3
import time
import urllib.request
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
t = c.get_transport()
if t:
    t.set_keepalive(20)

sftp = c.open_sftp()
sftp.put("docker-compose.lexhub.yml", "/opt/sanad/docker-compose.lexhub.yml")
sftp.close()

# remove broken/empty .next that triggers next start
_, o, _ = c.exec_command(
    "rm -rf /opt/sanad/frontend/.next; "
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "up -d --force-recreate frontend 2>&1"
)
print(o.read().decode(errors="replace")[-1500:])

for i in range(24):
    time.sleep(5)
    _, o2, _ = c.exec_command(
        "docker ps --filter name=sanad-frontend --format '{{.Status}}'; "
        "curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/login 2>/dev/null || echo 000"
    )
    out = o2.read().decode(errors="replace").strip()
    print(f"poll {i+1}:", out)
    if "Up" in out and "Restarting" not in out and out.endswith("200"):
        break

c.close()

try:
    r = urllib.request.urlopen("https://lexhub.space/login", timeout=30)
    print("public", r.status)
except Exception as e:
    print("public ERR", e)
