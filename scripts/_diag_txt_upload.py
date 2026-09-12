#!/usr/bin/env python3
"""Diagnose .txt upload rejection on VPS."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python <<'PY'
from app.services.extraction import ALLOWED_EXTENSIONS, ALLOWED_MIMES, get_extension
from app.services.file_sniff import sniff_allowed_upload

print('ext', repr(get_extension('test.txt')))
print('allowed_ext', '.txt' in ALLOWED_EXTENSIONS)
print('mime_plain', 'text/plain' in ALLOWED_MIMES)
print('sniff_utf8', sniff_allowed_upload('مرحبا\n'.encode('utf-8'), '.txt'))
# UTF-16 like Windows Notepad default for some locales
utf16 = 'مرحبا العالم'.encode('utf-16')
print('utf16_nulls', utf16[:40].count(b'\x00'), 'sniff', sniff_allowed_upload(utf16, '.txt'))
print('empty', sniff_allowed_upload(b'', '.txt'))
src = open('/app/app/api/documents.py', encoding='utf-8').read()
print('has_txt_mime', 'ext == ".txt"' in src)
PY
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
