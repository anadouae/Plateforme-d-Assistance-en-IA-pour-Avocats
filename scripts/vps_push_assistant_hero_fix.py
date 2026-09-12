#!/usr/bin/env python3
"""Deploy confirm X, assistant UX, hero brand video."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/ui/confirm-dialog.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/components/home/video-carousel.tsx",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/lib/i18n/translations.ts",
]


def run(c, cmd, timeout=90):
    print(">>", cmd[:180], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-2000:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend",
    90,
)
time.sleep(8)
c.close()
print("DONE", flush=True)
