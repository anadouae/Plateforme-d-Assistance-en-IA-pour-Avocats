#!/usr/bin/env python3
"""Hot-patch session UX, plaidoirie dossier obligatoire, digest, thème, copy."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

BACKEND_FILES = [
    "backend/app/api/dictation.py",
    "backend/app/api/notifications.py",
    "backend/app/services/billing.py",
    "backend/app/services/plaidoirie_case_compose.py",
]

FRONTEND_FILES = [
    "frontend/src/hooks/use-ui-prefs.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/legal-content.ts",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/aide/page.tsx",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/app/confidentialite/page.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/redaction/[templateId]/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/layout/public-session-bar.tsx",
    "frontend/src/components/layout/theme-toggle.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/plea-step-carousel.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/home/home-page-content.tsx",
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
run(c, "curl -sS -o /dev/null -w 'aide:%{http_code} tarifs:%{http_code}\\n' https://lexhub.space/aide https://lexhub.space/tarifs")
c.close()
print("DONE")
