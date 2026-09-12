#!/usr/bin/env python3
"""Deploy export UX: logo, esignature option, X + nouvelle plaidoirie."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/schemas/__init__.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "backend/app/api/plaidoirie_templates.py",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/lib/api.ts",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 18
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.docx_export import build_plaidoirie_docx
from app.services.pdf_export import build_plaidoirie_pdf
# tiny 1x1 png
png = bytes.fromhex(
  '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489'
  '0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082'
)
d, fn = build_plaidoirie_docx(
  title='اختبار', body='نص تجريبي\n\nأولاً: في الوقائع\nمحتوى.',
  cabinet_name='مكتب تجريبي', lawyer_name='دعاء', city='Casablanca',
  cabinet_logo_bytes=png, include_esignature=True,
)
assert fn.endswith('.docx') and len(d) > 1000, (fn, len(d))
print('docx_ok', len(d))
try:
  p, pfn = build_plaidoirie_pdf(
    title='اختبار', body='نص تجريبي\n\nأولاً: في الوقائع\nمحتوى.',
    cabinet_name='مكتب تجريبي', lawyer_name='دعاء', city='Casablanca',
    cabinet_logo_bytes=png, include_esignature=True,
  )
  assert p.startswith(b'%PDF'), p[:20]
  print('pdf_ok', len(p), pfn)
except Exception as e:
  print('pdf_skip_or_err', type(e).__name__, e)
print('SMOKE_OK')
PY
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-900:])
c.close()
print("DONE")
