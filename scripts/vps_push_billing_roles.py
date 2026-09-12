#!/usr/bin/env python3
"""Push billing role UX + restart frontend (dev volume mount — no rebuild)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/components/billing/ask-admin-billing.tsx",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:240])
    chan = c.get_transport().open_session()
    chan.settimeout(timeout)
    chan.exec_command(cmd)
    out_chunks = []
    err_chunks = []
    while True:
        if chan.recv_ready():
            out_chunks.append(chan.recv(65536))
        if chan.recv_stderr_ready():
            err_chunks.append(chan.recv_stderr(65536))
        if chan.exit_status_ready():
            while chan.recv_ready():
                out_chunks.append(chan.recv(65536))
            while chan.recv_stderr_ready():
                err_chunks.append(chan.recv_stderr(65536))
            break
    code = chan.recv_exit_status()
    out = b"".join(out_chunks).decode(errors="replace")
    err = b"".join(err_chunks).decode(errors="replace")
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-5000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    _, o, _ = c.exec_command(f"mkdir -p {parent}")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart frontend 2>&1 | tail -15",
    120,
)
run(
    c,
    "sleep 8; curl -sS -o /dev/null -w 'tarifs=%{http_code}\\n' https://lexhub.space/tarifs",
    40,
)
c.close()
print("DONE")
