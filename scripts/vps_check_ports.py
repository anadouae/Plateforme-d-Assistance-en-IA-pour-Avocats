#!/usr/bin/env python3
import os
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "51.38.78.23",
    username="root",
    password=os.environ["VPS_SSH_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
cmds = [
    "ss -tlnp | grep -E ':3000|:8001' || true",
    'docker ps -a --format "{{.Names}} {{.Status}} {{.Ports}}"',
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps",
]
for cmd in cmds:
    print(">>>", cmd)
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode() or e.read().decode())
c.close()
