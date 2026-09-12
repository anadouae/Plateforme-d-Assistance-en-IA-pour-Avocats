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
sftp = c.open_sftp()
sftp.put(
    r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\alembic\versions\001_initial.py",
    "/opt/sanad/backend/alembic/versions/001_initial.py",
)
sftp.close()
cmd = """cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend sh -lc 'cd /app && alembic upgrade head'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python scripts/seed_test_accounts.py
"""
_, o, e = c.exec_command(cmd, timeout=600)
code = o.channel.recv_exit_status()
print(o.read().decode())
if err := e.read().decode():
    print(err)
print("exit", code)
c.close()
