#!/usr/bin/env python3
"""Deploy enterprise UX: delete preview, admin audit, assistant dashboard, 48h agenda reminders."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/admin.py",
    "backend/app/schemas/__init__.py",
    "backend/app/models/__init__.py",
    "backend/app/main.py",
    "backend/app/services/agenda_reminders.py",
    "backend/app/services/celery_app.py",
    "backend/app/services/email.py",
    "backend/app/services/tasks.py",
    "backend/alembic/versions/023_agenda_reminder_48h.py",
    "docker-compose.yml",
    "docker-compose.lexhub.yml",
    "frontend/src/components/ui/confirm-dialog.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/app/admin/logs/page.tsx",
    "frontend/src/app/dashboard/page.tsx",
    "frontend/src/lib/i18n/translations.ts",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:180])
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
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing local file: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

# Recreate backend + frontend + celery-worker + celery-beat
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend celery-worker celery-beat 2>&1 | tail -40",
    timeout=600,
)

# Wait and verify migration applied / reminder module importable
run(
    c,
    f"cd {REMOTE} && sleep 12 && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend python -c \"from app.services.agenda_reminders import send_due_agenda_reminders; "
    f"from app.models import AgendaEvent; assert hasattr(AgendaEvent, 'reminder_48h_sent_at'); print('ok reminders')\" 2>&1",
    timeout=120,
)

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"ps backend frontend celery-worker celery-beat 2>&1 | tail -20",
    timeout=60,
)

c.close()
print("done")
