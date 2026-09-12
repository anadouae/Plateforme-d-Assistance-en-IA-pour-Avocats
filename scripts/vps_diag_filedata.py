#!/usr/bin/env python3
"""Diagnose document FileDataError on VPS."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
cd /opt/sanad
echo '=== recent failed docs ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T postgres \
  psql -U sanad -d sanad -c "SELECT id, original_name, status, left(coalesce(error_message,''),180) AS err, updated_at FROM documents WHERE status='failed' ORDER BY updated_at DESC LIMIT 8;" 2>&1 | tail -40

echo '=== backend logs FileData / OCR / failed ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --tail 400 2>&1 \
  | grep -iE 'FileData|OCR|extract|failed|mistral|gemini|pipeline|error' \
  | tail -80
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-800:])
c.close()
