#!/usr/bin/env python3
"""Deploy: no silent fact deletion + تم=extract."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation.py",
    "backend/app/services/dictation_contradictions.py",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -8
sleep 14
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation_contradictions import (
    _extract_case_numbers, _extract_dates, _extract_age_ranges,
    preserve_source_facts, restore_source_names, detect_dictation_contradictions,
    list_missing_source_facts,
)

src = (
    "ملف 125 جلسة 15 يوليوز 2026 الضحية ضحى بنت ليلى "
    "بين 15 وال 25 سنة تجارة البشر"
)
pol = (
    "جلسة الضحية ضحى بنت الليلة بنت ليلى تجارة البشر"
)
assert "125" in _extract_case_numbers(src), _extract_case_numbers(src)
assert any("يوليوز" in d for d in _extract_dates(src)), _extract_dates(src)
assert _extract_age_ranges(src), _extract_age_ranges(src)
fixed = restore_source_names(src, pol)
assert "الليلة" not in fixed or "ضحى بنت ليلى" in fixed, fixed
kept = preserve_source_facts(src, pol)
assert "125" in kept or "ملف" in kept, kept
assert any("يوليوز" in kept for _ in [1]) or "2026" in kept, kept
alerts = detect_dictation_contradictions(kept, source=src)
kinds = {a.kind for a in alerts}
print("cases", _extract_case_numbers(src))
print("dates", _extract_dates(src))
print("ages", _extract_age_ranges(src))
print("kept", kept[:200])
print("kinds", sorted(kinds))
print("missing_pre", list_missing_source_facts(src, pol))
assert "missing_fact" in kinds or "125" in kept
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
