#!/usr/bin/env python3
"""Deploy polish UX: case numbers, highlight levels, single preview, motion."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation_contradictions.py",
    "backend/app/services/dictation.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -8
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation_contradictions import (
    _extract_case_numbers,
    detect_dictation_contradictions,
    preserve_source_facts,
    annotate_stt_guesses,
)

src = (
    "ان ان الضحية ليلى بنت علي في الملف رقم 45 على 12 "
    "جلسة 10 من شهر شتنبر 2024 ثم ليلى بنت العلي ورقم 210 سنة 2026 بيع المقدات"
)
assert "210" in _extract_case_numbers(src) and "45/12" in _extract_case_numbers(src), _extract_case_numbers(src)
pol = "الضحية ليلى بنت علي في الملف رقم 210 جلسة 10 من شهر شتنبر 2024 ثم ليلى بنت العلي سنة 2026 بيع المقدمات"
kept = preserve_source_facts(src, pol)
alerts = detect_dictation_contradictions(kept, source=src)
kinds = {a.kind for a in alerts}
print("cases", _extract_case_numbers(src))
print("kept", kept[:120])
print("kinds", sorted(kinds))
assert "case_number" in kinds
assert "person_name" in kinds
marked, guessed = annotate_stt_guesses("بيع المقدات", "بيع المقدمات بسرعة")
assert "المقدمات" in guessed and "بسرعة" not in guessed, guessed
print("SMOKE_OK", guessed)
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-900:])
c.close()
print("DONE")
