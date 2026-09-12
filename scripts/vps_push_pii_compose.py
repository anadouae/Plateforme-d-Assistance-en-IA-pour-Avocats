#!/usr/bin/env python3
"""Deploy: PII always + legal identity in compose + UX confidentialité."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/pii_mask.py",
    "backend/app/services/plaidoirie_case_compose.py",
    "backend/app/services/billing.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 12
python3 - <<'PY'
from pathlib import Path
c = Path('backend/app/services/plaidoirie_case_compose.py').read_text(encoding='utf-8')
p = Path('backend/app/services/pii_mask.py').read_text(encoding='utf-8')
w = Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8')
print('always_pii', 'use_pii = bool(parties)' in c)
print('legal_block', '_legal_identity_block' in c)
print('variants', '_name_variants' in p)
print('ux_conf', 'PARTIE_A' in w and '3 sources' in w)
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-400:])
c.close()
print("DONE")
