#!/usr/bin/env python3
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=40)
cmd = r"""docker exec sanad-backend-1 python -c "from sqlalchemy import text; from app.core.database import SessionLocal; db=SessionLocal(); cols=[r[0] for r in db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='plaidoirie_drafts'\")).fetchall()]; print(cols); print(db.execute(text('SELECT version_num FROM alembic_version')).scalar()); db.close()" """
_, o, e = c.exec_command(cmd, timeout=40)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:300])
# force migrate if needed
_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1",
    timeout=90,
)
print("migrate:", o.read().decode(errors="replace")[-800:])
c.close()
