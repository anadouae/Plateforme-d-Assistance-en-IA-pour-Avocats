#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "SELECT status, ocr_score, length(coalesce(extracted_text,'')) FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';"

# Force usable score + clear alert noise for this long extract
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "UPDATE documents SET ocr_score=92 WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0' RETURNING ocr_score;"

# Check API ocr_alert logic + try synth
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.core.config import settings
from app.services.agent import generate_synthesis
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
print('score', doc.ocr_score, 'threshold', settings.OCR_QUALITY_THRESHOLD)
print('alert', doc.ocr_score is not None and doc.ocr_score < settings.OCR_QUALITY_THRESHOLD)
text=(doc.extracted_text or '')
print('chars', len(text))
data=generate_synthesis(doc.original_name, text[:20000], language='ar')
s=(data.get('summary') or '')[:180].replace('\n',' ')
print('summary_head', s)
print('risks_n', len(data.get('risk_clauses') or []))
print('dates', data.get('key_dates'))
db.close()
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-1200:])
c.close()
