import paramiko
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / "backend/app/api/admin.py"), "/opt/sanad/backend/app/api/admin.py")
sftp.close()
_, o, e = c.exec_command(
    "cd /opt/sanad; docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart backend 2>&1 | tail -5",
    timeout=60,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
print("done")
