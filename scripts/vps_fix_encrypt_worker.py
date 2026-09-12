#!/usr/bin/env python3
"""Sync ENCRYPTION_KEY on celery-worker to match backend, recreate, reextract failed PDF."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
set -e
cd /opt/sanad

# Pull the working key from the backend container (do not echo it)
BKEY=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv ENCRYPTION_KEY | tr -d '\r')
WKEY=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker printenv ENCRYPTION_KEY | tr -d '\r')
python3 - <<PY
b='''$BKEY'''
w='''$WKEY'''
print('before_same', b==w, 'b_len', len(b.strip()), 'w_len', len(w.strip()), 'b_prefix', b[:6], 'w_prefix', w[:6])
PY

# Update root .env ENCRYPTION_KEY to match backend (files were encrypted with backend key)
python3 - <<'PY'
from pathlib import Path
import subprocess
b = subprocess.check_output(
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv ENCRYPTION_KEY",
    shell=True, cwd="/opt/sanad",
).decode().strip().replace("\r","")
env_path = Path("/opt/sanad/.env")
text = env_path.read_text(encoding="utf-8", errors="replace")
lines = []
found = False
for line in text.splitlines():
    if line.startswith("ENCRYPTION_KEY="):
        lines.append(f"ENCRYPTION_KEY={b}")
        found = True
    else:
        lines.append(line)
if not found:
    lines.append(f"ENCRYPTION_KEY={b}")
env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("updated .env ENCRYPTION_KEY")
# also backend/.env if present
bp = Path("/opt/sanad/backend/.env")
if bp.exists():
    t = bp.read_text(encoding="utf-8", errors="replace")
    lines=[]
    found=False
    for line in t.splitlines():
        if line.startswith("ENCRYPTION_KEY="):
            lines.append(f"ENCRYPTION_KEY={b}")
            found=True
        else:
            lines.append(line)
    if not found:
        lines.append(f"ENCRYPTION_KEY={b}")
    bp.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("updated backend/.env ENCRYPTION_KEY")
PY

# Recreate celery-worker so it picks up the env
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate celery-worker 2>&1 | tail -15
sleep 8

WKEY2=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker printenv ENCRYPTION_KEY | tr -d '\r')
python3 - <<PY
b='''$BKEY'''
w='''$WKEY2'''
print('after_same', b.strip()==w.strip(), 'w_prefix', w[:6])
PY

echo '=== worker can decrypt PDF? ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.object_storage import read_file
db = SessionLocal()
doc = db.query(Document).filter(Document.id == '0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
content = read_file(doc.storage_path)
print('magic', content[:8], 'bytes', len(content))
import fitz
d = fitz.open(stream=content, filetype='pdf')
print('pages', len(d), 'ok')
d.close()
db.close()
PY

echo '=== requeue process_document ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document, DocumentStatus
from app.services.tasks import process_document
db = SessionLocal()
doc = db.query(Document).filter(Document.id == '0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
doc.status = DocumentStatus.PENDING
doc.error_message = None
db.commit()
db.close()
r = process_document.delay('0566cb46-cb05-4b8f-b0ce-9b06300d07a0')
print('queued', r.id)
PY

sleep 25
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "SELECT status, left(coalesce(error_message,''),120) AS err, length(coalesce(extracted_text,'')) AS chars FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';" 2>&1

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs celery-worker --tail 40 2>&1 | grep -iE '0566cb46|FileData|indexed|failed|permanently|text ready|OCR' | tail -25
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-2000:])
c.close()
