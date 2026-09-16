#!/usr/bin/env python3
"""Deploy revise: answer+edit, Annuler/Modifier, micro, meta QCM explain."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/api/dictation.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/api.ts",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.plaidoirie_revise import (
    _wants_explain, _wants_meta_pipeline, _wants_fill_gaps, _SYSTEM,
)
s = "d ou vient ce formulaire de questions et comment se preparent"
assert _wants_explain(s) and _wants_meta_pipeline(s)
s2 = "veux comprendr e xplqiue moi خامساً : لهذه الأسباب :الملتمسات"
assert _wants_explain(s2)
assert "ASSISTANT_REPLY" in _SYSTEM
assert "formulaire" in _SYSTEM.lower() or "QCM" in _SYSTEM
print("SMOKE_OK")
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
