#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/extraction.py",
    "backend/app/services/agent.py",
    "frontend/src/components/ai/synthesis-panel.tsx",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -4
sleep 10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.extraction import extract_dates, extract_risk_clauses
sample = '''ظهير رقم 1.74.447 بتاريخ 1974 و القانون 1.02.298 و 4096/1/4 و 2018/1/1 و 24/12/2019
لنجاعة والسرعة الإجرائية لفائدة الدائنين مسؤولية البيع الجبري
يعتبر البيع الجبري مسطرة دقيقة ويترتب على مخالفتها البطلان عند الإخلال بالضمانات.
'''
print('dates', extract_dates(sample))
print('risks', extract_risk_clauses(sample))
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=150)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
print("DONE")
