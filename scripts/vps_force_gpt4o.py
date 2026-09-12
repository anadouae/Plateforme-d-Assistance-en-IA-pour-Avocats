#!/usr/bin/env python3
"""Force OPENAI_MODEL=gpt-4o on VPS + redeploy polish."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
sftp.put(str(ROOT / "backend/app/services/dictation.py"), f"{REMOTE}/backend/app/services/dictation.py")
print("ok dictation.py")
sftp.close()

remote_sh = r"""
cd /opt/sanad
for f in .env .env.vps; do
  [ -f "$f" ] || continue
  if grep -q '^OPENAI_MODEL=' "$f"; then
    sed -i 's/^OPENAI_MODEL=.*/OPENAI_MODEL=gpt-4o/' "$f"
  else
    echo 'OPENAI_MODEL=gpt-4o' >> "$f"
  fi
  if grep -q '^DICTATION_POLISH_USE_LLM=' "$f"; then
    sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' "$f"
  else
    echo 'DICTATION_POLISH_USE_LLM=true' >> "$f"
  fi
done
echo '--- env ---'
grep -E '^OPENAI_MODEL=|^DICTATION_POLISH_USE_LLM=' .env .env.vps 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -25
sleep 4
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.core.config import settings; print('MODEL', settings.OPENAI_MODEL); print('POLISH', settings.DICTATION_POLISH_USE_LLM)"
"""
_, o, e = c.exec_command(remote_sh, timeout=400)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr:", err[-1200:])
c.close()
print("done")
