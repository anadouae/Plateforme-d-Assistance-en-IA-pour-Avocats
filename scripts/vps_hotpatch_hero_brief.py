#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND_FILES = [
    "backend/app/api/dictation.py",
    "backend/app/services/plaidoirie_case_compose.py",
]
FRONTEND_FILES = [
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/home/landing-waveform.tsx",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/compose-progress.tsx",
]
BACKEND_CONTAINERS = ("sanad-backend-1", "sanad-celery-worker-1", "sanad-celery-beat-1")


def run(c, cmd, timeout=180):
    print(">>", cmd[:200])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    print(o.read().decode(errors="replace")[-2000:])
    print("exit", o.channel.recv_exit_status())


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in BACKEND_FILES + FRONTEND_FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname '{remote}')")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()
for rel in BACKEND_FILES:
    container_path = "/app/" + rel.replace("backend/", "", 1)
    for name in BACKEND_CONTAINERS:
        run(c, f"docker cp '{REMOTE}/{rel}' {name}:{container_path}")
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12",
)
c.close()
print("DONE")
