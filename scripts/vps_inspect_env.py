#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=30)

cmds = [
    "ls -la /opt/sanad/.env* 2>&1",
    "wc -l /opt/sanad/.env; head -5 /opt/sanad/.env; echo '---'; grep -c SECRET /opt/sanad/.env || true",
    "docker exec sanad-backend-1 printenv | grep -E '^(ENVIRONMENT|SECRET_KEY|ENCRYPTION_KEY|SMTP_|TURNSTILE_SITE|SEED_)' | sed -E 's/(SECRET_KEY|ENCRYPTION_KEY|PASSWORD)=.*/\\1=***/'",
]
for cmd in cmds:
    print(f"$ {cmd}")
    _, o, e = c.exec_command(cmd)
    print(o.read().decode(errors="replace") or e.read().decode(errors="replace"))
    print()
c.close()
