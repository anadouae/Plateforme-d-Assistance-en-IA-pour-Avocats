#!/usr/bin/env python3
import paramiko
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
import re
from app.core.database import SessionLocal
from app.models import Document
from app.services.extraction import arabic_char_ratio, _strip_word, _line_reading_score
db=SessionLocal()
text=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first().extracted_text or ''
print('frag', bool(re.search(r'(العقا\b|،?\s*رية\b|المعامالت|المعامﻼت|صصُخ|زّويمي|قّالموث|الّوفع)', text)))
words=[_strip_word(w) for w in text.split()]; words=[w for w in words if w]
tiny=sum(1 for w in words if len(w)<=1)
print('tiny_ratio', round(tiny/len(words),3), 'tiny', tiny)
lines=[ln.strip() for ln in text.splitlines() if len(ln.split())>=4]
bad=sum(1 for ln in lines if ln[:1] in '،.؛!?ًٌٍَُِّْ')
print('lines', len(lines), 'bad_start_ratio', round(bad/max(1,len(lines)),3))
orig=sum(_line_reading_score(ln.split()) for ln in lines)
rev=sum(_line_reading_score(list(reversed(ln.split()))) for ln in lines)
print('orig', orig, 'rev', rev, 'threshold', max(10,len(lines)*3), 'rev_wins', rev>orig+max(10,len(lines)*3))
print('rev/orig', round(rev/max(1,orig),3))
db.close()
PY
"""
_,o,e=c.exec_command(cmd, timeout=90)
print(o.read().decode(errors='replace'))
c.close()
