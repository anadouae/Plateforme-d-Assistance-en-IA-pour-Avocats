#!/usr/bin/env python3
"""Deploy: domains + templates non-destructif."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/lib/case-domains.ts",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/components/redaction/template-picker.tsx",
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/dictation.py",
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
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.plaidoirie_prompt import PLAIDOIRIE_TYPES, build_plaidoirie_system
for tid in ["circulation","fiscal","detention","banque-credit","penal-ordinaire"]:
    assert tid in PLAIDOIRIE_TYPES, tid
sys = build_plaidoirie_system("famille")
assert "غير مدمّر" in sys or "Non-Destructif" in sys or "ممنوع منعاً باتاً" in sys
print("types", len(PLAIDOIRIE_TYPES))
print("SMOKE_DOMAINS_OK")
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
