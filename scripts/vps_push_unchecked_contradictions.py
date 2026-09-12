#!/usr/bin/env python3
"""Deploy: never claim 'no contradictions' when check did not run; fix polish return path."""
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation, _collapse_repeats
from app.services.dictation_contradictions import detect_dictation_contradictions

src = (
    "ان ان الضحية ليلى بنت علي في الملف رقم 45 على 12 "
    "جلسة 10 من شهر شتنبر 2024 ثم ليلى بنت العلي والملف رقم 210 سنة 2026"
)
collapsed = _collapse_repeats(src)
assert not collapsed.startswith("ان ان"), collapsed[:40]
polished, prov = polish_dictation(src, language="ar", source="audio")
assert polished is not None and len(polished) > 10, (polished, prov)
alerts = detect_dictation_contradictions(polished, source=src)
kinds = {a.get("kind") for a in alerts}
print("provider:", prov)
print("collapsed_ok:", not collapsed.startswith("ان ان"), "->", collapsed[:50])
print("alerts:", len(alerts), sorted(kinds))
print("sample:", [a.get("kind") for a in alerts][:6])
assert len(alerts) >= 1, alerts
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
