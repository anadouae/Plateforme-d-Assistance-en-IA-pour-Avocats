#!/usr/bin/env python3
"""Force-recreate backend/celery/frontend with new DATABASE_URL; fix celery image; seed passwords."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / "docker-compose.yml"), f"{REMOTE}/docker-compose.yml")
sftp.close()

cmd = r"""
cd /opt/sanad
# show DATABASE_URL host part only
python3 - <<'PY'
from pathlib import Path
import re
t=Path('.env.vps').read_text()
m=re.search(r'^DATABASE_URL=(.*)$', t, re.M)
print('DATABASE_URL_SET', bool(m))
if m:
    u=m.group(1)
    print('DB_URL_SAFE', u.split('@')[-1] if '@' in u else u)
    print('USER', u.split('://')[1].split(':')[0] if '://' in u else '?')
PY
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --force-recreate --no-deps backend celery-worker celery-beat frontend 2>&1 | tail -40
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DATABASE_URL | sed 's#://[^@]*@#://***@#'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python scripts/seed_test_accounts.py 2>&1 | tail -25
curl -sf https://lexhub.space/health && echo
curl -s -o /tmp/opsdb.html -w 'ops_db:%{http_code}\n' https://lexhub.space/_ops/db/
head -c 200 /tmp/opsdb.html; echo
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()
print("DONE")
