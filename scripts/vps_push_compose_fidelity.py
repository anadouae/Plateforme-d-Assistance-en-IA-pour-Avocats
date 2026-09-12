#!/usr/bin/env python3
"""Deploy compose fidelity fix (no truncation / no hallucination)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_postprocess.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/free_llm_router.py",
    "scripts/_smoke_compose_fidelity.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
for f in plaidoirie_postprocess.py dictation.py plaidoirie_prompt.py free_llm_router.py; do
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp backend/app/services/$f backend:/app/app/services/$f
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -3
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml cp scripts/_smoke_compose_fidelity.py backend:/tmp/_smoke_compose_fidelity.py
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T -e PYTHONPATH=/app -w /app backend python /tmp/_smoke_compose_fidelity.py 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1500:])
c.close()
print("DONE")
