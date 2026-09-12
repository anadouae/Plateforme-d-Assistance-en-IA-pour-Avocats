#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation_assist.py",
    "frontend/src/components/redaction/plea-assist-panel.tsx",
    "frontend/src/styles/sanad-ui.css",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -6
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation
from app.services.dictation_assist import build_assist_payload
src = (
    "انا المربع التي نحن ان المرافعة التي نحن بصدد القائها سيدي الرئيس "
    "المدعية حنيا بنت محمد بكريان اولاد الفقراء بين 16 وال 25 سنة ملف رقم 120"
)
pol, _ = polish_dictation(src, language="ar")
assist = build_assist_payload(src, pol)
assert len(assist["edits"]) >= 3, assist["edits"]
print("edits", len(assist["edits"]))
for e in assist["edits"][:5]:
    print(e["kind"], e["original"][:35], "->", e["proposed"][:35])
print("SMOKE_EDITS_OK")
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
print("DONE")
