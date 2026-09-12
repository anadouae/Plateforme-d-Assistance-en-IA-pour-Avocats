#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
sftp.put(str(ROOT / "backend/app/services/extraction.py"), "/opt/sanad/backend/app/services/extraction.py")
sftp.close()
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend celery-worker 2>&1 | tail -6
sleep 8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.extraction import is_scrambled_arabic
from app.core.config import settings
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
print('scrambled', is_scrambled_arabic(doc.extracted_text or ''))
print('score', doc.ocr_score, 'alert', doc.ocr_score is not None and doc.ocr_score < settings.OCR_QUALITY_THRESHOLD)
db.close()
PY
"""
_,o,e=c.exec_command(cmd, timeout=120)
print(o.read().decode(errors='replace'))
print(e.read().decode(errors='replace')[-400:])
c.close()
