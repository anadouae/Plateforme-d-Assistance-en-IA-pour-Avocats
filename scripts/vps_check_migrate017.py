#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic current
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from sqlalchemy import text, inspect
from app.core.database import engine
insp = inspect(engine)
cols = {c["name"] for c in insp.get_columns("cabinets")}
tables = set(insp.get_table_names())
print("logo_path", "logo_path" in cols)
print("name_ar", "name_ar" in cols)
print("drafts", "plaidoirie_drafts" in tables)
print("full_name_ar users", any(c["name"]=="full_name_ar" for c in insp.get_columns("users")))
PY
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-600:])
c.close()
