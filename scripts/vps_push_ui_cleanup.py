#!/usr/bin/env python3
"""Push UI: no Chrome labels / audio upload; infinite analysis; download %."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/ai/document-status-badge.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p '/opt/sanad/frontend/src/app/documents/[id]' '/opt/sanad/frontend/src/app/cases/[id]'"
)
o.read()
e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -8
sleep 14
python3 - <<'PY'
from pathlib import Path
p = Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8')
bad = ['ابدأ (Chrome)', 'ملف صوتي', 'Chrome مباشرة', 'Commencer (Chrome)']
found = [b for b in bad if b in p]
print('chrome_labels:', found or 'gone')
print('indet:', 'ocr-bar--indeterminate' in Path('frontend/src/styles/sanad-ui.css').read_text(encoding='utf-8'))
print('progress:', 'onProgress' in Path('frontend/src/lib/api.ts').read_text(encoding='utf-8'))
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-600:])
c.close()
print("DONE")
