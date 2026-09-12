#!/usr/bin/env python3
"""Hot-patch: marketing pro (no demo), about/security, nudges, dark contrast, seats."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND_FILES = [
    "backend/app/services/retention_lifecycle.py",
]

FRONTEND_FILES = [
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/home/landing-waveform.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/app/about/page.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/app/aide/page.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/components/billing/smart-insights-strip.tsx",
    "frontend/src/components/billing/visitor-convert-nudge.tsx",
    "frontend/src/components/billing/plans-nudge-modal.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
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

# Remove obsolete public session bar if still on VPS
try:
    sftp.remove(f"{REMOTE}/frontend/src/components/layout/public-session-bar.tsx")
    print("removed public-session-bar.tsx")
except OSError:
    pass

sftp.close()

for rel in BACKEND_FILES:
    container_path = "/app/" + rel.replace("backend/", "", 1)
    for name in BACKEND_CONTAINERS:
        run(c, f"docker cp '{REMOTE}/{rel}' {name}:{container_path}")

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -20",
)
c.close()
print("DONE")
