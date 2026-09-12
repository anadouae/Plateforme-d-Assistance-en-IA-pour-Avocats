#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/home/landing-royal-test.css",
    "frontend/src/components/home/hero-serpent-b.tsx",
    "frontend/src/components/home/landing-trust-band.tsx",
    "frontend/src/components/home/landing-feature-icon.tsx",
    "frontend/src/components/home/landing-pricing-carousel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate frontend 2>&1 | tail -15",
    timeout=300,
)
print((o.read() + e.read()).decode(errors="replace")[-2000:])
print("exit", o.channel.recv_exit_status())
c.close()
print("done")
