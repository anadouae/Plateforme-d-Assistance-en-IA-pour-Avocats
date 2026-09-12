#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres psql -U sanad -d sanad -c "
SELECT status,
       length(coalesce(extracted_text,'')) AS full_chars,
       left(coalesce(error_message,''),80) AS err,
       ocr_score
FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';
"

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.api import documents as docs_api
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
t=doc.extracted_text or ''
print('status', doc.status, 'ocr', doc.ocr_score)
print('full_len', len(t))
print('preview_slice_2000_ends_with_ellipsis_in_ui', len(t)>=2000)
# first/last windows
print('--- HEAD ---')
print(t[:500].replace('\n',' | '))
print('--- MID ---')
mid=max(0,len(t)//2)
print(t[mid:mid+300].replace('\n',' | '))
print('--- TAIL ---')
print(t[-500:].replace('\n',' | '))
# count pages markers / intro markers
for needle in ['مقدمة','خاتمة','المبحث الأول','الفهرس','البيوعات العقارية القضائية','كلية العلوم']:
    print(needle, t.count(needle))
# check reversed-looking (common: starts with French then arabic backwards)
print('starts', repr(t[:80]))
db.close()
PY
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()
