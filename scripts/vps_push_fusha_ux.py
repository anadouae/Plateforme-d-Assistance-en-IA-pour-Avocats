#!/usr/bin/env python3
"""Deploy: تم=extract only; تصحيح=fusha LLM+guards; local fusha fallback."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_contradictions.py",
    "backend/app/services/arabic_text_fix.py",
    "docker-compose.lexhub.yml",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
for f in .env .env.vps; do
  [ -f "$f" ] || continue
  grep -q '^DICTATION_POLISH_USE_LLM=' "$f" \
    && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' "$f" \
    || echo 'DICTATION_POLISH_USE_LLM=true' >> "$f"
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d backend 2>&1 | tail -15
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -6
sleep 20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.arabic_text_fix import light_arabic_fusha_form
from app.services.dictation import polish_dictation

raw = (
    "ان المرافعة التي نحن بصدد القائها سيدي الرئيس تخص قضية من قضايا جرائم الاتجار بالمخدرات "
    "والتي تورط الاشخاص ان الملف الذي نحن بصدد علاجه وتقديمه اليوم هو ملف رقم 180 "
    "وتاريخ الجلسة 18 يوليوز 2023"
)
local = light_arabic_fusha_form(raw)
assert "إن المرافعة" in local, local[:100]
assert "إلقائها" in local, local
assert "الأشخاص" in local, local
assert "180" in local and "2023" in local
pol, prov = polish_dictation(raw, language="ar", source="audio")
assert "180" in pol and "2023" in pol
print("provider", prov)
print("local", local[:180])
print("pol", pol[:180])
print("SMOKE_FUSHA_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=360)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1500:])
c.close()
print("DONE")
