#!/usr/bin/env python3
"""Deploy: hide noisy risk_clauses; summary-first synthesis UI."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/ai/synthesis-panel.tsx",
    "backend/app/services/agent.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 12
python3 - <<'PY'
from pathlib import Path
fe = Path('frontend/src/components/ai/synthesis-panel.tsx').read_text(encoding='utf-8')
be = Path('backend/app/services/agent.py').read_text(encoding='utf-8')
print('no_risk_ui', 'بنود المخاطر' not in fe or 'risk_clauses.length' not in fe)
print('summary_first', 'labels.executive' in fe and fe.find('labels.executive') < fe.find('structuredHint'))
print('risks_empty', '"risk_clauses": []' in be and 'extract_risk_clauses(text)' not in be.split('def generate_synthesis')[1].split('def generate_case')[0])
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-500:])
c.close()
print("DONE")
