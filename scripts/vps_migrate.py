#!/usr/bin/env python3
import os
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "51.38.78.23",
    username="root",
    password=os.environ["VPS_SSH_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
cmd = """cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python scripts/seed_test_accounts.py
curl -sf https://lexhub.space/health/live || curl -sf http://127.0.0.1:8001/health/live
echo MIGRATE_OK
"""
_, o, e = c.exec_command(cmd, timeout=600)
code = o.channel.recv_exit_status()
print(o.read().decode()[-5000:])
if err := e.read().decode():
    print(err[-2000:])
print("exit", code)
c.close()
