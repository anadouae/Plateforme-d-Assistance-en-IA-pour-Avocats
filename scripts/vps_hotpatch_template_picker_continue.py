#!/usr/bin/env python3
"""Hot-patch TemplatePicker UX: selection + continue button, no preview modal."""

from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/redaction/template-picker.tsx",
]

BACKEND_CONTAINERS = ()
FRONTEND_CONTAINERS = ("sanad-frontend-1",)


def run(c, cmd, timeout=300):
    print(">>", cmd[:240])
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

for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname '{remote}')")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)

sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -20",
    timeout=180,
)

c.close()
print("DONE")

