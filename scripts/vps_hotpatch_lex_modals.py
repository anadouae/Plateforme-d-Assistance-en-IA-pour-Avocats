#!/usr/bin/env python3
"""Hot-patch: Lex product modals + dark banners + security page."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/billing/lex-product-modal.tsx",
    "frontend/src/components/billing/visitor-convert-nudge.tsx",
    "frontend/src/components/billing/plans-nudge-modal.tsx",
    "frontend/src/components/billing/trial-pitch-modal.tsx",
    "frontend/src/components/billing/auth-gate-modal.tsx",
    "frontend/src/components/billing/payment-success-modal.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/billing/smart-insights-strip.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/app/about/page.tsx",
]


def run(c, cmd, timeout=300):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-3000:])
    if err.strip():
        print("stderr:", err[-1000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
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
