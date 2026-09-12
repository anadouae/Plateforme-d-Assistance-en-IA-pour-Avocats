#!/usr/bin/env python3
"""Deploy: fiche juridique dossier + parcours plaidoirie sans écran matière/type."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/alembic/versions/029_case_legal_identity.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/cases.py",
    "frontend/src/lib/case-legal.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/plea-session.ts",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/redaction/new/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/alembic/versions "
    "/opt/sanad/backend/app/api "
    "/opt/sanad/frontend/src/lib "
    "/opt/sanad/frontend/src/components/cases "
    "/opt/sanad/frontend/src/components/redaction "
    "/opt/sanad/frontend/src/app/redaction/new "
    "'/opt/sanad/frontend/src/app/cases/[id]'"
)
o.read()
e.read()
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend alembic upgrade head 2>&1 | tail -20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -15
sleep 16
python3 - <<'PY'
from pathlib import Path
ws = Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8')
newp = Path('frontend/src/app/redaction/new/page.tsx').read_text(encoding='utf-8')
mod = Path('backend/app/models/__init__.py').read_text(encoding='utf-8')
print('act_type_ui', 'Type d’acte à produire' in ws or 'نوع الوثيقة لهذه المرة' in ws)
print('no_matiere_type_screen', 'matière & type' not in newp.lower() and 'redaction/libre' in newp)
print('jurisdiction_col', 'jurisdiction_degree' in mod)
print('case_legal_lib', Path('frontend/src/lib/case-legal.ts').exists())
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'api:%{http_code}\n' https://lexhub.space/api/health || true
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
