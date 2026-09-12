#!/usr/bin/env python3
"""Deploy hero S3, morocco courts, admin center, past_due grace, agenda lieu."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/home/landing-royal-test.css",
    "frontend/src/components/home/video-carousel.tsx",
    "frontend/src/lib/morocco-courts.ts",
    "frontend/src/lib/case-legal.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/settings/admin-cabinet-center.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/components/ui/confirm-dialog.tsx",
    "frontend/src/styles/sanad-ui.css",
    "backend/alembic/versions/030_court_city_agenda_lieu.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/cases.py",
    "backend/app/api/workspace.py",
    "backend/app/api/billing.py",
    "backend/app/services/billing.py",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:200], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-3500:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel, flush=True)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -20",
    120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart backend frontend 2>&1 | tail -20",
    120,
)
time.sleep(10)
run(
    c,
    "curl -sS -o /dev/null -w 'home=%{http_code}\\n' https://lexhub.space/",
    40,
)
c.close()
print("DONE", flush=True)
