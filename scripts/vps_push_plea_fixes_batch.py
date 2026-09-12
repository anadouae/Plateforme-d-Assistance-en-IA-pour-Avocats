#!/usr/bin/env python3
"""Deploy: plea fixes, txt upload, Q&A, export PDF download, delete draft."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/ai/document-ask.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/lib/api.ts",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/docx_export.py",
    "backend/app/api/documents.py",
    "backend/app/api/plaidoirie_templates.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/frontend/src/components/ai "
    "/opt/sanad/frontend/src/components/redaction "
    "/opt/sanad/frontend/src/app/redaction "
    "/opt/sanad/frontend/src/app/documents "
    "/opt/sanad/frontend/src/lib "
    "/opt/sanad/backend/app/services "
    "/opt/sanad/backend/app/api"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -15
sleep 14
python3 - <<'PY'
from pathlib import Path
print('delete_draft', 'draft_delete' in Path('backend/app/api/plaidoirie_templates.py').read_text(encoding='utf-8'))
print('txt_mime', 'ext == ".txt"' in Path('backend/app/api/documents.py').read_text(encoding='utf-8'))
print('pdf_dl', 'downloadOfficialArabicHtml' in Path('frontend/src/lib/export-official-doc.ts').read_text(encoding='utf-8'))
print('doc_ask', 'StructuredSynthesis' in Path('frontend/src/components/ai/document-ask.tsx').read_text(encoding='utf-8'))
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
