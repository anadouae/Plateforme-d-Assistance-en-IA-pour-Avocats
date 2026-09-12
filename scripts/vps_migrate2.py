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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend sh -lc 'cd /app && alembic upgrade head 2>&1'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend sh -lc 'cd /app && python -c "from app.core.migrations import run_migrations; run_migrations(); print(\"migrations ok\")"'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python scripts/seed_test_accounts.py 2>&1
"""
_, o, e = c.exec_command(cmd, timeout=600)
code = o.channel.recv_exit_status()
print(o.read().decode())
print(e.read().decode())
print("exit", code)
c.close()
