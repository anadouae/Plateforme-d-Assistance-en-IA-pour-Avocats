#!/usr/bin/env python3
"""Deploy: real local fusḥā form + STT orange marks + UX honesty."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_assist.py",
    "backend/tests/test_dictation_pipeline.py",
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
    && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=false/' "$f" \
    || echo 'DICTATION_POLISH_USE_LLM=false' >> "$f"
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -20
sleep 22
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.arabic_text_fix import light_arabic_fusha_form
from app.services.dictation import polish_dictation

raw = (
    "إن المرافعة التي نحن بصدد إلقائها تخص قضية من قضايا عن التجار بالمخدرات "
    "والتي كانت قد تورطت فيها عدد من الأشخاص"
)
local = light_arabic_fusha_form(raw)
assert "‹الاتجار بالمخدرات›" in local, local
plain = local.replace("‹", "").replace("›", "")
assert "تورط فيها عدد" in plain, plain
assert "تورطت فيها عدد" not in plain
pol, prov = polish_dictation(raw, language="ar", source="audio")
assert prov == "fidelity", prov
assert "‹الاتجار بالمخدرات›" in pol, pol
assert "إعدادها" in light_arabic_fusha_form("نحن بصدد أيدادها اليوم أمام المحكمة الموقرة")
print("provider", prov)
print("pol", pol)
print("SMOKE_FUSHA_REAL_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-2000:])
c.close()
print("DONE")
