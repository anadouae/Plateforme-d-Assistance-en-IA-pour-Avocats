#!/usr/bin/env python3
"""Deploy real PDF export (PyMuPDF + Noto fonts)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/pdf_export.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/assets/NotoNaskhArabic-Regular.ttf",
    "backend/app/assets/NotoNaskhArabic-Bold.ttf",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/app/redaction/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/app/services /opt/sanad/backend/app/api "
    "/opt/sanad/backend/app/assets /opt/sanad/frontend/src/lib "
    "/opt/sanad/frontend/src/components/redaction /opt/sanad/frontend/src/app/redaction"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.is_file():
        raise SystemExit(f"missing {rel}")
    sftp.put(str(local), f"{REMOTE}/{rel}")
    print("ok", rel, local.stat().st_size)
sftp.close()

cmd = r"""
cd /opt/sanad
# sync fonts into running container if volume-mounted differently
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 16
python3 - <<'PY'
from pathlib import Path
print('pdf_svc', Path('backend/app/services/pdf_export.py').is_file())
print('font_reg', Path('backend/app/assets/NotoNaskhArabic-Regular.ttf').stat().st_size)
print('api_pdf', 'export-pdf' in Path('backend/app/api/plaidoirie_templates.py').read_text(encoding='utf-8'))
print('fe_pdf', 'downloadPlaidoiriePdf' in Path('frontend/src/lib/api.ts').read_text(encoding='utf-8'))
PY
# smoke: import inside backend container
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \
  python -c "from app.services.pdf_export import build_plaidoirie_pdf; b,n=build_plaidoirie_pdf(title='مرافعة تجريبية', body='أولاً — في الوقائع\n\nنص تجريبي.\n\nثانياً — في المناقشة\n\nمناقشة.\n\nلهذه الأسباب\n\n1. الطلب.'); print(n, len(b), b[:4])" 2>&1 | tail -20
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
