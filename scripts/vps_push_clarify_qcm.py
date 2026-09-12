#!/usr/bin/env python3
"""Deploy: PII smart + clarify QCM + sheet UI."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/pii_mask.py",
    "backend/app/services/plaidoirie_case_compose.py",
    "backend/app/services/plaidoirie_clarify.py",
    "backend/app/api/dictation.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plea-clarify-sheet.tsx",
    "frontend/src/components/redaction/compose-progress.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/app/services /opt/sanad/backend/app/api "
    "/opt/sanad/frontend/src/lib /opt/sanad/frontend/src/components/redaction"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 14
python3 - <<'PY'
from pathlib import Path
print('clarify_svc', Path('backend/app/services/plaidoirie_clarify.py').exists())
print('clarify_route', '/clarify' in Path('backend/app/api/dictation.py').read_text(encoding='utf-8'))
print('collect_names', 'collect_all_party_names' in Path('backend/app/services/pii_mask.py').read_text(encoding='utf-8'))
print('sheet', Path('frontend/src/components/redaction/plea-clarify-sheet.tsx').exists())
print('ws_clarify', 'startClarifyFlow' in Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8'))
print('progress_clarify', 'Clarification avocat' in Path('frontend/src/components/redaction/compose-progress.tsx').read_text(encoding='utf-8'))
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=200)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-500:])
c.close()
print("DONE")
