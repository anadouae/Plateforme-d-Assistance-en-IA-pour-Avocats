#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation, _collapse_repeats
from app.services.dictation_contradictions import detect_dictation_contradictions

src = (
    "ان ان الضحية ليلى بنت علي في الملف رقم 45 على 12 "
    "جلسة 10 من شهر شتنبر 2024 ثم ليلى بنت العلي والملف رقم 210 سنة 2026"
)
collapsed = _collapse_repeats(src)
print("collapsed_dup_gone:", not collapsed.startswith("ان ان"), "|", collapsed[:60])
polished, prov = polish_dictation(src, language="ar", source="audio")
print("provider:", prov, "len:", len(polished or ""))
assert polished and len(polished) > 10
alerts = detect_dictation_contradictions(polished, source=src)
print("alerts:", [(a.kind, a.values) for a in alerts])
assert len(alerts) >= 1
print("SMOKE_OK")
PY
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
