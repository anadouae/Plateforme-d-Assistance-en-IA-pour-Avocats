#!/usr/bin/env python3
"""Hot-patch billing checkout + simulation."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND_FILES = [
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
]

FRONTEND_FILES = [
    "frontend/src/lib/checkout-draft.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/plan-cta.ts",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/components/billing/payment-success-modal.tsx",
    "frontend/src/components/billing/card-brand-badges.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/layout/legal-page-layout.tsx",
]

BACKEND_CONTAINERS = ("sanad-backend-1", "sanad-celery-worker-1", "sanad-celery-beat-1")


def run(c, cmd, timeout=300):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("stderr:", err[-1500:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()

for rel in BACKEND_FILES + FRONTEND_FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
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
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart backend celery-worker celery-beat frontend 2>&1 | tail -20",
    timeout=180,
)
run(c, "curl -sS -o /dev/null -w 'checkout:%{http_code}\\n' https://lexhub.space/checkout?plan=pro")
c.close()
print("DONE")
