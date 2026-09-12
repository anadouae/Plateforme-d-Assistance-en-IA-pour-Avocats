#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --tail 120 2>&1 | tail -80
"""
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace")[-4000:])
c.close()
