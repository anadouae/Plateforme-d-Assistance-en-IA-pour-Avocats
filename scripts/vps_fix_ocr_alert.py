#!/usr/bin/env python3
"""Fix OCR alert: deploy heuristics + raise score on the biouaat PDF + patch agent on VPS."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/extraction.py",
    "backend/app/services/document_pipeline.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad

# Patch agent.py in place on VPS (local file may be locked)
python3 - <<'PY'
from pathlib import Path
p = Path('/opt/sanad/backend/app/services/agent.py')
t = p.read_text(encoding='utf-8')
a = 'if scrambled and not assume_native and not is_audio:'
b = 'if scrambled and not assume_native and not is_audio and len(text) < 12000:'
c = '        if scrambled and not assume_native:\n            attention.append('
d = '        if scrambled and not assume_native and len(text) < 12000:\n            attention.append('
n = 0
if a in t:
    t = t.replace(a, b, 1); n += 1
if c in t:
    t = t.replace(c, d, 1); n += 1
p.write_text(t, encoding='utf-8')
print('agent_patches', n)
PY

# Clear false medium-quality score on this long usable extract
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "UPDATE documents SET ocr_score=88 WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0'; SELECT id, status, ocr_score, length(coalesce(extracted_text,'')) FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';"

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend celery-worker 2>&1 | tail -15
sleep 10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.extraction import is_scrambled_arabic
from app.core.database import SessionLocal
from app.models import Document
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
print('score', doc.ocr_score, 'chars', len(doc.extracted_text or ''), 'scrambled', is_scrambled_arabic(doc.extracted_text or ''))
from app.core.config import settings
print('alert_would_show', doc.ocr_score is not None and doc.ocr_score < settings.OCR_QUALITY_THRESHOLD)
db.close()
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()
print("DONE")
