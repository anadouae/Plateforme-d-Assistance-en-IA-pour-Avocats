#!/usr/bin/env python3
"""Deploy P1bis: forme-only polish (no content merge) + idea coverage."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_contradictions.py",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -6
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation_contradictions import (
    extract_idea_phrases,
    list_missing_source_facts,
    content_word_coverage,
    preserve_source_facts,
    detect_dictation_contradictions,
)

src = (
    "عصابة فيها رجل وامراتين وتتكون من ثمانية اشخاص "
    "تجارة البشر وايجار البشر بالمخدرات والاتجار بالبشر "
    "باقسم العقوبات بين 15 وال 25 سنة ملف رقم 125 "
    "ضحى بنت ليلى تعويضا تشديد العقوبات جلسة 15 يوليوز 2026"
)
bad = "عصابة من ثمانية أشخاص وايجار المخدرات. قسم العقوبات."
ideas = extract_idea_phrases(src)
assert "رجل وامرأتان" in ideas, ideas
assert "إيجار البشر" in ideas, ideas
miss = list_missing_source_facts(src, bad)
miss_vals = {v for _, v in miss}
assert "رجل وامرأتان" in miss_vals, miss
assert "إيجار البشر" in miss_vals, miss
assert content_word_coverage(src, bad) < 0.68
kept = preserve_source_facts(src, bad)
assert "رجل وامرأتان" in kept or "عناصر" in kept, kept
alerts = detect_dictation_contradictions(kept, source=src)
kinds = {a.kind for a in alerts}
assert "missing_fact" in kinds, kinds
# Prompt forme/fond present
from app.services import dictation as d
assert "دمج" in d.POLISH_SYSTEM_AR or "تلخيص" in d.POLISH_SYSTEM_AR
assert "شكل" in d.POLISH_SYSTEM_AR
print("ideas", ideas)
print("miss", sorted(miss_vals))
print("SMOKE_OK_FORME_FOND")
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
