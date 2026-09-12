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
cmd = r"""cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres psql -U sanad -d sanad -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import Base, engine
import app.models  # noqa: F401
Base.metadata.create_all(bind=engine)
print("tables ok")
PY
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend sh -lc 'cd /app && alembic stamp head'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python scripts/seed_test_accounts.py
echo BOOTSTRAP_OK
"""
_, o, e = c.exec_command(cmd, timeout=600)
code = o.channel.recv_exit_status()
print(o.read().decode())
if err := e.read().decode():
    print(err[-3000:])
print("exit", code)
c.close()
