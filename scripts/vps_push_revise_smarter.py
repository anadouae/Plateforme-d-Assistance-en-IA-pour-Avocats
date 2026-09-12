#!/usr/bin/env python3
"""Deploy smarter plaidoirie revise (interpret typos, force real edits)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_revise.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -8
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.plaidoirie_revise import _changed_enough, _parse_title_body, _SYSTEM
assert 'سيدي الرئيس' in _SYSTEM
assert _changed_enough('abc '*50, 'xyz '*50)
assert not _changed_enough('hello world '*10, 'hello world '*10)
t,b=_parse_title_body('TITLE: T\nBODY:\nنص معدل طويل جدا '*20,'old','old body')
assert t=='T' and 'نص' in b
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-600:])
c.close()
print("DONE")
