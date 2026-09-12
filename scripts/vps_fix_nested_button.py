#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
rel = "frontend/src/components/home/landing-pricing-carousel.tsx"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
sftp.close()
print("sftp ok")

# Confirm fix on disk
_, o, _ = c.exec_command(
    f"grep -n 'motion.div\\|motion.button' {REMOTE}/{rel} | head -5"
)
print(o.read().decode(errors="replace"))

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1",
    timeout=90,
)
print(o.read().decode(errors="replace")[-1200:])
print("stderr:", e.read().decode(errors="replace")[-500:])
print("exit", o.channel.recv_exit_status())

_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps frontend --format '{{{{.Status}}}}'"
)
print("status:", o.read().decode(errors="replace").strip())
c.close()
print("DONE")
