#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation_contradictions.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/api/dictation.py",
    "backend/app/services/dictation.py",
    "docker-compose.lexhub.yml",
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
grep -q '^DICTATION_POLISH_USE_LLM=' .env 2>/dev/null && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=false/' .env || true
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d backend 2>&1 | tail -8
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation
from app.services.dictation_contradictions import detect_dictation_contradictions, list_missing_source_facts
raw = (
    "ان المرافعة التي نحن بصدد القائها سيدي الرئيس تخص قضية من قضايا جرائم الاتجار بالمخدرات "
    "والتجارة بالبشر والتي تورطت فيها عصابة فيها رجل وامراتين وتتكون من ثمانية اشخاص "
    "وايجار البشر بالمخدرات والاتجار بالبشر ولذلك باقسم العقوبات "
    "بين 15 وال 25 سنة ملف رقم 125 تاريخ الجلسة 15 يوليوز 2026 ضحى بنت ليلى"
)
pol, prov = polish_dictation(raw, language="ar", source="audio")
assert prov == "fidelity", prov
assert "125" in pol and "رجل" in pol
miss = list_missing_source_facts(raw, pol)
print("miss", miss)
alerts = detect_dictation_contradictions(pol, source=raw)
print("kinds", [a.kind for a in alerts])
assert not any(a.kind == "missing_fact" for a in alerts), [(a.kind, a.values) for a in alerts]
print("pol", pol[:240])
print("SMOKE_OK")
PY
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1000:])
c.close()
print("DONE")
