#!/usr/bin/env python3
import paramiko
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
cmd = r"""
cd /opt/sanad
grep -n 'Long mémoire\|len(text) >= 12000' backend/app/services/extraction.py | head -10
grep -n 'len(text) < 12000' backend/app/services/agent.py | head -5
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.extraction import is_scrambled_arabic, arabic_char_ratio
db=SessionLocal()
t=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first().extracted_text or ''
words=t.split()
print('chars', len(t), 'words', len(words), 'ar_ratio', round(arabic_char_ratio(t),3))
legal=sum(1 for m in ('القانون','الظهير','مدونة','المحكمة','المادة','الفصل','المشرع','المسطرة','التنفيذ') if m in t)
print('legal', legal, 'scrambled', is_scrambled_arabic(t))
db.close()
PY
"""
_,o,e=c.exec_command(cmd, timeout=90)
print(o.read().decode(errors='replace'))
print(e.read().decode(errors='replace')[-400:])
c.close()
