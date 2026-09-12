#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/api/documents.py",
    "backend/app/services/agent.py",
    "backend/app/services/extraction.py",
    "backend/app/services/document_pipeline.py",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()
cmd = r"""
cd /opt/sanad
# keep score high for this doc
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "UPDATE documents SET ocr_score=92 WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';"
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -10
sleep 8
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
print("DONE")
