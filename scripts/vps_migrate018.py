#!/usr/bin/env python3
import paramiko
import time

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60)
time.sleep(3)
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend alembic upgrade head 2>&1",
    timeout=120,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:400])
_, o, _ = c.exec_command(
    "docker exec sanad-backend-1 python -c \"from app.models import PlaidoirieDraft; print('status', hasattr(PlaidoirieDraft,'status'))\"",
    timeout=30,
)
print(o.read().decode(errors="replace"))
c.close()
