#!/usr/bin/env python3
"""Deploy export aperçu + revise IA + hide classify + navbar Mon espace."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/api/dictation.py",
    "backend/app/services/plaidoirie_revise.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/plaidoirie-document-preview.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing {rel}")
    sftp.put(str(local), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 20
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.api.dictation import ReviseRequest, revise_plaidoirie
from app.services.plaidoirie_revise import revise_plaidoirie_body
print('revise_ok', callable(revise_plaidoirie_body))
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
