#!/usr/bin/env python3
import time
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

# push hardened decrypt
sftp = c.open_sftp()
sftp.put(
    r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\object_storage.py",
    "/opt/sanad/backend/app/services/object_storage.py",
)
sftp.close()
print("pushed object_storage.py")

for i in range(24):
    _, o, _ = c.exec_command(
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres "
        "psql -U sanad -d sanad -t -A -c \"SELECT status || '|' || length(coalesce(extracted_text,'')) || '|' || left(coalesce(error_message,''),80) FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0';\"",
        timeout=60,
    )
    line = o.read().decode(errors="replace").strip()
    print(f"[{i}] {line}")
    if line.startswith("INDEXED") or line.startswith("FAILED"):
        break
    time.sleep(15)

_, o, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs celery-worker --tail 60 2>&1 | grep -iE '0566cb46|indexed|failed|OCR|text ready|permanently|Mistral' | tail -30",
    timeout=60,
)
print(o.read().decode(errors="replace"))
c.close()
