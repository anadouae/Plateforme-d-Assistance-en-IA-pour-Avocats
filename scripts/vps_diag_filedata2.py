#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== services ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps --format '{{.Name}} {{.Status}}' 2>&1

echo '=== failed docs ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "SELECT id, left(original_name,50) AS name, status, left(coalesce(error_message,''),200) AS err, created_at FROM documents WHERE status='failed' OR error_message ILIKE '%FileData%' ORDER BY created_at DESC LIMIT 10;" 2>&1

echo '=== doc detail ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "SELECT id, original_name, mime_type, file_size, storage_path, status, error_message FROM documents WHERE id='0566cb46-cb05-4b8f-b0ce-9b06300d07a0' OR original_name ILIKE '%بيع%' ORDER BY created_at DESC LIMIT 5;" 2>&1

echo '=== worker logs ==='
for s in worker celery backend; do
  echo "-- $s --"
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs $s --tail 250 2>&1 | grep -iE 'FileData|Traceback|Error|failed permanently|process_document|0566cb46|fitz|mistral|pdf' | tail -40
done
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-500:])
c.close()
