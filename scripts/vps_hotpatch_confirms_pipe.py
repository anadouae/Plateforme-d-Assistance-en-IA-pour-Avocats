#!/usr/bin/env python3
"""Hot-patch: billing-panel syntax, confirms, plea pipeline, assistant copy."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/billing/confirm-action-modal.tsx",
    "frontend/src/components/billing/lex-product-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/components/redaction/plea-step-carousel.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print(out[-2000:] if out.strip() else "", err[-800:] if err.strip() else "")
    print("exit", o.channel.recv_exit_status())


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname '{remote}')")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("sftp", rel)
sftp.close()
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -12",
)
c.close()
print("DONE")
