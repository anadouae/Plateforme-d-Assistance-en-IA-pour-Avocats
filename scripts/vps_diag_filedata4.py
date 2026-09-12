#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== pymupdf versions ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "import pymupdf,sys; print('backend', pymupdf.__version__, sys.version)"
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker python -c "import pymupdf,sys; print('worker', pymupdf.__version__, sys.version)"

echo '=== open PDF in celery-worker ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.object_storage import read_file
import traceback
db = SessionLocal()
doc = db.query(Document).filter(Document.id == '0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
content = read_file(doc.storage_path)
print('bytes', len(content), 'magic', content[:8], 'eof', b'%%EOF' in content[-2048:])
try:
    import fitz
    d = fitz.open(stream=content, filetype='pdf')
    print('worker fitz OK', len(d), 'encrypted', d.is_encrypted)
    # try first page text
    print('page0 chars', len(d[0].get_text() or ''))
    d.close()
except Exception as e:
    print('WORKER_FAIL', type(e).__name__, e)
    traceback.print_exc()

# full extract path
try:
    from app.services.extraction import extract_from_pdf
    text, score = extract_from_pdf(content)
    print('extract chars', len(text or ''), 'score', score, 'preview', (text or '')[:120].replace('\n',' '))
except Exception as e:
    print('EXTRACT_FAIL', type(e).__name__, e)
    traceback.print_exc()
db.close()
PY
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-2000:])
c.close()
