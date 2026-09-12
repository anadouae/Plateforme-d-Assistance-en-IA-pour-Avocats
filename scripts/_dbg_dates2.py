#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
# write exact sample into container via stdin
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python <<'PY'
from app.services.dictation_contradictions import detect_dictation_contradictions, _extract_dates
sample = (
    "ان ان المربع ان الذين اعترفوا بكل ما نسب اليهم الذين اعترفوا بكل ما نسب اليهم "
    "في ملف رقم 20 على 28 بتاريخ 20/28 ثم ملف رقم 105 "
    "والجلسة 18 من شهر اغسطس 2023 2026 والمتهم فاطمة"
)
print('dates', _extract_dates(sample))
print('alerts', [(a.kind, a.values) for a in detect_dictation_contradictions(sample)])
# show snippet around جلسة
i = sample.find('جلسة')
print('snip', repr(sample[i-5:i+50]) if i>=0 else 'no')
PY
"""
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
