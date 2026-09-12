#!/usr/bin/env python3
"""Deploy UX/billing/plaidoirie header fixes (bind mounts + restart)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/settings/admin-cabinet-center.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/onboarding/profile-completion-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/lib/landing-faq.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/admin/logs/page.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "backend/app/services/billing.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/api/admin.py",
    "backend/app/api/auth.py",
    "backend/app/api/settings.py",
    "backend/app/schemas/__init__.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("MISSING", rel)
        continue
    sftp.put(str(local), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend frontend celery-worker 2>&1 | tail -15
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend python - <<'PY'
from app.services.billing import MOROCCO_PAYMENT_METHODS
assert not any(m['id']=='virement' for m in MOROCCO_PAYMENT_METHODS), MOROCCO_PAYMENT_METHODS
print('no_virement_ok', [m['id'] for m in MOROCCO_PAYMENT_METHODS])
from app.services.docx_export import _add_letterhead
import inspect
sig=str(inspect.signature(_add_letterhead))
assert 'cabinet_name_ar' in sig
print('letterhead_ok')
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code} tarifs:%{http_code}\n' https://lexhub.space/ https://lexhub.space/tarifs
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-1500:])
c.close()
print("DONE")
