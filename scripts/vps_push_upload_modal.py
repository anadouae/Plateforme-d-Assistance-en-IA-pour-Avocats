#!/usr/bin/env python3
"""Deploy: upload modal (file first), txt/case-ref fix, remove Open from history."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/api/cases.py",
    "backend/app/services/file_sniff.py",
    "backend/app/api/documents.py",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/app/api /opt/sanad/backend/app/services "
    "/opt/sanad/frontend/src/app/documents /opt/sanad/frontend/src/app/redaction "
    "/opt/sanad/frontend/src/styles"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 14
python3 - <<'PY'
from pathlib import Path
print('modal', 'upload-dest-overlay' in Path('frontend/src/styles/sanad-ui.css').read_text(encoding='utf-8'))
print('page_modal', 'confirmDestinationUpload' in Path('frontend/src/app/documents/page.tsx').read_text(encoding='utf-8'))
print('no_open_btn', 'chip-btn primary' not in Path('frontend/src/app/redaction/page.tsx').read_text(encoding='utf-8').split('drafts.map')[1][:800] if 'drafts.map' in Path('frontend/src/app/redaction/page.tsx').read_text(encoding='utf-8') else 'n/a')
print('ref_fix', 'max_n' in Path('backend/app/api/cases.py').read_text(encoding='utf-8'))
print('txt_early', 'UTF-16' in Path('backend/app/services/file_sniff.py').read_text(encoding='utf-8'))
PY
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python <<'PY'
from app.services.file_sniff import sniff_allowed_upload
from app.api.cases import _generate_reference
from app.core.database import SessionLocal
assert sniff_allowed_upload(b'hi', '.txt') is None
assert sniff_allowed_upload('مرحبا'.encode('utf-8'), '.txt') is None
db = SessionLocal()
print('next_ref', _generate_reference(db))
db.close()
print('sniff_ok')
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
