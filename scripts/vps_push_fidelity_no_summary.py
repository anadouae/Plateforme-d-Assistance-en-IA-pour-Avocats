#!/usr/bin/env python3
"""Deploy: stop LLM summary — fidelity polish + no false date/name alerts."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_contradictions.py",
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
# Forcer aussi dans .env / .env.vps
for f in .env .env.vps; do
  [ -f "$f" ] || continue
  grep -q '^DICTATION_POLISH_USE_LLM=' "$f" \
    && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=false/' "$f" \
    || echo 'DICTATION_POLISH_USE_LLM=false' >> "$f"
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d backend 2>&1 | tail -12
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation
from app.services.dictation_contradictions import (
    list_missing_source_facts,
    detect_dictation_contradictions,
    strip_reinjection_notes,
)

src = (
    "عصابة فيها رجل وامراتين ملف رقم 125 بين 15 وال 25 سنة "
    "جلسة 15 يوليوز 2026 ضحى بنت ليلى باقسم العقوبات "
    "ايجار البشر بالمخدرات والاتجار بالبشر"
)
pol, prov = polish_dictation(src, language="ar")
assert prov == "fidelity", prov
assert "125" in pol
assert "رجل" in pol
assert "يوليوز" in pol or "2026" in pol
# Pas d'alerte date/nom inventée
fake = pol + " ضحى بنت أيوب جلسة 15 يونيو 2024"
alerts = detect_dictation_contradictions(fake, source=src)
kinds = {a.kind for a in alerts}
assert "date" not in kinds, kinds
assert "person_name" not in kinds, kinds
# Corps LLM résumé → missing détecté
bad = "عصابة وايجار المخدرات. قسم العقوبات."
assert list_missing_source_facts(src, bad)
print("provider", prov)
print("pol_snip", pol[:120])
print("SMOKE_FIDELITY_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1000:])
c.close()
print("DONE")
