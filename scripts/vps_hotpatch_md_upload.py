#!/usr/bin/env python3
"""Allow .md uploads — hotpatch frontend + backend."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND = [
    "backend/app/services/extraction.py",
    "backend/app/services/file_sniff.py",
    "backend/app/api/documents.py",
]
FRONTEND = [
    "frontend/src/components/documents/document-upload.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/lib/i18n/translations.ts",
]
BACKEND_CONTAINERS = ("sanad-backend-1", "sanad-celery-worker-1")


def run(c, cmd, timeout=300):
    print(">>", cmd[:200])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-2500:])
    if err.strip():
        print("stderr:", err[-800:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in BACKEND + FRONTEND:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()

for rel in BACKEND:
    container_path = "/app/" + rel.replace("backend/", "", 1)
    for name in BACKEND_CONTAINERS:
        run(c, f"docker cp '{REMOTE}/{rel}' {name}:{container_path}")

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart backend celery-worker frontend 2>&1 | tail -25",
    timeout=180,
)
c.close()
print("DONE")
