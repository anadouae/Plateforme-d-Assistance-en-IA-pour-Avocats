#!/usr/bin/env python3
from pathlib import Path
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "docker logs sanad-backend-1 --tail 120 2>&1 | grep -iE 'team|/api/team|invite|entitlement|Error|Traceback' | tail -50",
    timeout=60,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
