#!/usr/bin/env python3
"""Deploy: remove Print; clean [] / duplicate signatures / fidelity."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
    "frontend/src/app/redaction/page.tsx",
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
from app.services.dictation import _clean_compose_body
from app.services.plaidoirie_layout import prepare_plaidoirie_blocks
raw = '''أولاً :— في الوقائع: نص. [] ثانياً : [] في المناقشة: نص.
لهذه الأسباب :/ الملتمسات: 1. طلب أ. 2. طلب ب.
صيغة الختام: تحت جميع التحفظات… حرر بـ Casablanca بتاريخ …… التوقيع ذ. ……
حرر بـ Casablanca
التوقيع
دعاء العسال
خاتم المحامي'''
c = _clean_compose_body(raw)
assert '[]' not in c, c
assert 'Casablanca' not in c, c
assert 'صيغة الختام' not in c, c
blocks = prepare_plaidoirie_blocks(c)
assert not any('توقيع' in b for b in blocks), blocks
assert not any('[]' in b for b in blocks), blocks
print('CLEAN_OK', blocks)
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
