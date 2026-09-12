#!/usr/bin/env python3
"""Deploy branding + planning + plaidoirie fixes to VPS."""
import paramiko

FILES = [
    "backend/alembic/versions/017_cabinet_branding_drafts.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/auth.py",
    "backend/app/api/settings.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/dictation.py",
    "backend/app/services/docx_export.py",
    "frontend/src/lib/demo-plaidoirie.ts",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/styles/sanad-ui.css",
]
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = f"""
cd {REMOTE}
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -30
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -15
sleep 6
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import _clean_compose_body
s = _clean_compose_body("جده وحيد، إننا نقدم لكم هذه المرافعة باسم موكلنا.")
assert "جده" not in s
assert "السيد رئيس المحكمة" in s or "إننا نقدم" in s
print("jadi_ok", s[:80])
from app.models import Cabinet, PlaidoirieDraft
print("models_ok", Cabinet.__tablename__, PlaidoirieDraft.__tablename__)
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace")[-2500:])
err = e.read().decode(errors="replace")[-800:]
if err:
    print("ERR", err)
c.close()
print("done")
