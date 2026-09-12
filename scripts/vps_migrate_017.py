#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
sftp = c.open_sftp()
sftp.put(
    "backend/alembic/versions/017_cabinet_branding_drafts.py",
    "/opt/sanad/backend/alembic/versions/017_cabinet_branding_drafts.py",
)
sftp.close()
_, o, e = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend alembic upgrade head 2>&1",
    timeout=90,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
