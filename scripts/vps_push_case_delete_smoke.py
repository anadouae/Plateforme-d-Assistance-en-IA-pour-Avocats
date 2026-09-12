#!/usr/bin/env python3
"""Deploy case-delete cascade fix + run smoke cleanup on demo cabinet."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/cases.py",
    "backend/scripts/cleanup_smoke_demo.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 | tail -20",
    timeout=300,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[:500])

# Wait for backend healthy-ish, then run cleanup inside container
_, o, e = c.exec_command(
    f"cd {REMOTE} && sleep 8 && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend python scripts/cleanup_smoke_demo.py 2>&1",
    timeout=180,
)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr:", err[:800])
c.close()
print("done")
