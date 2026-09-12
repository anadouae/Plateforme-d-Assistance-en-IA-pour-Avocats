#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
import re
from app.services.dictation_contradictions import _extract_dates, _extract_case_numbers
t = 'والجلسة 18 من شهر اغسطس 2023 2026 ملف رقم 20 على 28 ثم ملف رقم 105 بتاريخ 20/28'
print('cases', _extract_case_numbers(t))
print('dates', _extract_dates(t))
print('month_hit', re.search(r'من\s+شهر\s+اغسطس', t))
"
"""
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
