#!/usr/bin/env python3
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "alembic history 2>&1 | head -40; echo ---; "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "alembic current 2>&1",
    timeout=60,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
