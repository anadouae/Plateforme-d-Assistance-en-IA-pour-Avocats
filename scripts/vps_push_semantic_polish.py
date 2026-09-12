#!/usr/bin/env python3
"""Deploy semantic polish + contradiction alerts."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_contradictions.py",
    "backend/app/api/dictation.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/app/services /opt/sanad/backend/app/api "
    "/opt/sanad/frontend/src/lib /opt/sanad/frontend/src/components/redaction "
    "/opt/sanad/frontend/src/styles"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
# upload smoke test file
smoke = ROOT / "scripts" / "_smoke_polish_contr.py"
sftp.put(str(smoke), f"{REMOTE}/scripts/_smoke_polish_contr.py")
print("ok smoke")
sftp.close()

cmd = r"""
cd /opt/sanad
mkdir -p scripts
grep -q '^DICTATION_POLISH_USE_LLM=' .env.vps 2>/dev/null \
  && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' .env.vps \
  || echo 'DICTATION_POLISH_USE_LLM=true' >> .env.vps
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \
  python /app/../scripts/_smoke_polish_contr.py 2>&1 || \
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \
  python -c 'exec(open("/opt/sanad/scripts/_smoke_polish_contr.py",encoding="utf-8").read())' 2>&1 || \
python3 /opt/sanad/scripts/_smoke_polish_contr.py 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=200)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
