#!/usr/bin/env python3
import paramiko
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "logs frontend --tail 40 2>&1; echo '---'; sleep 8; curl -sI https://lexhub.space/ | head -5; "
    "curl -sI https://lexhub.space/api/health | head -10",
    timeout=60,
)
print(o.read().decode(errors="replace")[-5000:])
c.close()
