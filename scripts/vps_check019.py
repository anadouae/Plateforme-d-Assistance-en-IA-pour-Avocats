#!/usr/bin/env python3
import paramiko
import time

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=40)
time.sleep(2)
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend alembic upgrade head 2>&1; "
    "docker exec sanad-backend-1 python -c \"from sqlalchemy import text; from app.core.database import SessionLocal; db=SessionLocal(); print('ver', db.execute(text('select version_num from alembic_version')).scalar()); print('tables', 'cabinet_notifications' in [r[0] for r in db.execute(text(\\\"select tablename from pg_tables where schemaname=\\\\'public\\\\'\\\")).fetchall()]); db.close()\"",
    timeout=90,
)
print(o.read().decode(errors="replace"))
c.close()
