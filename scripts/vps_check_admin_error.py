#!/usr/bin/env python3
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
grep -n adminPlatform frontend/src/lib/i18n/translations.ts | head
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs frontend --tail 120 2>&1 | tail -80
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()
