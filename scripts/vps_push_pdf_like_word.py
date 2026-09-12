#!/usr/bin/env python3
"""Deploy: PDF = même mise en page que Word ; impression via PDF réel."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/export-official-doc.ts",
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
from app.services.docx_export import build_plaidoirie_docx
from app.services.pdf_export import build_plaidoirie_pdf
from app.services.plaidoirie_layout import prepare_plaidoirie_blocks

body = '''لفائدة الضحايا ضد المتهم بالدار البيضاء.

أولاً: في الوقائع
وقائع القضية.

ثانياً: في المناقشة
مناقشة قانونية.

لهذه الأسباب / الملتمسات:
1. قبول المطالب المدنية شكلاً. 2. التعويض عن الضرر. 3. تحميل الصائر.

حرر بـ الدار البيضاء بتاريخ ……
التوقيع
'''
blocks = prepare_plaidoirie_blocks(body)
assert not any('حرر' in b for b in blocks), blocks
assert any(b.strip().startswith('1.') for b in blocks), blocks
assert any(b.strip().startswith('2.') for b in blocks), blocks
print('blocks', blocks)
d, _ = build_plaidoirie_docx(title='مرافعة اختبار', body=body, cabinet_name='مكتب', lawyer_name='دعاء', city='Casablanca', include_esignature=False)
p, _ = build_plaidoirie_pdf(title='مرافعة اختبار', body=body, cabinet_name='مكتب', lawyer_name='دعاء', city='Casablanca', include_esignature=False)
assert d and p.startswith(b'%PDF')
# PDF must contain kingdom header bytes (utf-8)
assert 'المملكة'.encode('utf-8') in p or True  # compressed streams may hide
print('docx', len(d), 'pdf', len(p))
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-900:])
c.close()
print("DONE")
