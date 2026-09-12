#!/usr/bin/env python3
"""Deploy smarter STT garbage cleanup."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -5
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation
raw = (
    "انا المربع التي نحن ان المرافعة التي نحن بصدد القائها سيدي الرئيس "
    "المدعية حنيا بنت محمد بكريان اولاد الفقراء بين 16 وال 25 سنة ملف رقم 120 "
    "تاريخ الجلسة 16 يوليو 2020"
)
pol, prov = polish_dictation(raw, language="ar")
assert pol.startswith("إن المرافعة"), pol[:80]
assert "انا المربع" not in pol
assert "120" in pol and "حنية" in pol
print("provider", prov)
print("pol", pol[:220])
print("SMOKE_SMART_OK")
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
if e.read().strip():
    print("err", e.read()[-500:])
c.close()
print("DONE")
