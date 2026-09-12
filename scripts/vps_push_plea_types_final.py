#!/usr/bin/env python3
"""Deploy plaidoirie types + upgrade UX all roles."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/dictation.py",
    "backend/app/services/dictation.py",
    "frontend/src/app/redaction/new/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:200])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-3500:])
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
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -25",
    timeout=300,
)
run(c, "sleep 12; curl -sS -o /dev/null -w 'home=%{http_code} new=%{http_code}\\n' https://lexhub.space/ https://lexhub.space/redaction/new")
c.close()
print("done")
