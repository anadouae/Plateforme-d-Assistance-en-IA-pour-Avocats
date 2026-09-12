#!/usr/bin/env python3
"""Reproduce FileDataError on the failing PDF from MinIO."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== celery container name ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps -a 2>&1 | head -30

echo '=== celery-worker full recent errors ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs celery-worker --tail 500 2>&1 | grep -iE 'FileData|Traceback|permanently|0566cb46|Error|Exception|process_document' | tail -80

echo '=== test open PDF inside backend ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.object_storage import read_file
import traceback

db = SessionLocal()
doc = db.query(Document).filter(Document.id == '0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
print('doc:', doc.original_name if doc else None, 'path:', doc.storage_path if doc else None)
content = read_file(doc.storage_path)
print('bytes:', len(content), 'magic:', content[:8])
try:
    import fitz
    d = fitz.open(stream=content, filetype='pdf')
    print('fitz OK pages', len(d), 'needs_pass', d.needs_pass, 'is_encrypted', d.is_encrypted)
    d.close()
except Exception as e:
    print('FITZ_FAIL', type(e).__name__, e)
    traceback.print_exc()

# try repair / ignore errors
try:
    import fitz
    d = fitz.open(stream=content, filetype='pdf')
except Exception:
    try:
        import fitz
        # some versions support repair
        d = fitz.open(stream=content, filetype='pdf')
    except Exception as e2:
        print('no open', e2)

# header sniff
print('header_ascii:', content[:64])
print('endswith_eof:', b'%%EOF' in content[-2048:])
db.close()
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-1500:])
c.close()
