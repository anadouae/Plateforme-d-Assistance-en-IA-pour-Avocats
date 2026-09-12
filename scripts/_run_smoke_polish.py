#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
# put smoke into mounted backend volume
sftp = c.open_sftp()
sftp.put(
    r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\scripts\_smoke_polish_contr.py",
    "/opt/sanad/backend/_smoke_polish_contr.py",
)
sftp.close()
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \
  python /app/_smoke_polish_contr.py 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \
  printenv DICTATION_POLISH_USE_LLM 2>&1
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
