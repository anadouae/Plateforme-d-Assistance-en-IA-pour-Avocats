#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/lib/plea-session.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/redaction/[templateId]/page.tsx",
    "frontend/src/app/redaction/new/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    # ensure remote dir exists for nested paths
    remote_dir = str(Path(remote).parent).replace("\\", "/")
    _, o, _ = c.exec_command(f"mkdir -p '{remote_dir}'")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart frontend 2>&1 | tail -20",
    timeout=180,
)
print(o.read().decode(errors="replace"))
print("exit", o.channel.recv_exit_status())
c.close()
print("DONE")
