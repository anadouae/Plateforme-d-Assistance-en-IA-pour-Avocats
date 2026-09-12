#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=45)
cmd = (
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python - <<'PY'\n"
    "from sqlalchemy import text\n"
    "from app.core.database import SessionLocal\n"
    "db = SessionLocal()\n"
    "cols = db.execute(text(\"select column_name from information_schema.columns "
    "where table_name='cases' and column_name in "
    "('court_file_number','notification_date','appeal_deadline_at') "
    "order by 1\")).fetchall()\n"
    "print('cases cols', cols)\n"
    "docs = db.execute(text(\"select column_name from information_schema.columns "
    "where table_name='documents' and column_name='inventory_number'\")).fetchall()\n"
    "print('doc inventory', docs)\n"
    "ver = db.execute(text('select version_num from alembic_version')).fetchall()\n"
    "print('alembic', ver)\n"
    "PY"
)
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("ERR", err[-800:])
c.close()
