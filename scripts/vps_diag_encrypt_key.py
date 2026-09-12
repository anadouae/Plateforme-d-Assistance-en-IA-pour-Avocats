#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== ENCRYPTION_KEY presence ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.core.config import settings; k=settings.ENCRYPTION_KEY or ''; print('backend key_len', len(k), 'prefix', k[:6] if k else None)"
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker python -c "from app.core.config import settings; k=settings.ENCRYPTION_KEY or ''; print('worker key_len', len(k), 'prefix', k[:6] if k else None)"

echo '=== env files / compose env ==='
grep -n 'ENCRYPTION\|celery-worker\|env_file' docker-compose.yml docker-compose.lexhub.yml 2>/dev/null | head -40
# compare env without printing secret
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv ENCRYPTION_KEY >/tmp/b.key 2>/dev/null
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker printenv ENCRYPTION_KEY >/tmp/w.key 2>/dev/null
python3 - <<'PY'
from pathlib import Path
b=Path('/tmp/b.key').read_bytes().strip()
w=Path('/tmp/w.key').read_bytes().strip()
print('backend_env_len', len(b), 'worker_env_len', len(w), 'same', b==w and len(b)>0)
PY
ls -la backend/.env .env 2>/dev/null | head -5
grep -c ENCRYPTION_KEY backend/.env .env 2>/dev/null || true
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()
