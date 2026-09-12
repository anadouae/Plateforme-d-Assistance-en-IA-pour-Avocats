#!/usr/bin/env python3
"""Deploy full retention emails P1-P3 + smart insights UX."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/email.py",
    "backend/app/services/retention_lifecycle.py",
    "backend/app/services/trial_lifecycle.py",
    "backend/app/services/celery_app.py",
    "backend/app/services/tasks.py",
    "backend/app/api/billing.py",
    "backend/app/api/team.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/billing/smart-insights-strip.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-4000:])
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
    f"up -d --force-recreate backend frontend celery-worker celery-beat 2>&1 | tail -35",
    timeout=360,
)
run(
    c,
    "sleep 14; curl -sS -o /dev/null -w 'home=%{http_code} insights_auth=%{http_code}\\n' "
    "https://lexhub.space/ https://lexhub.space/api/billing/insights; "
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python -c \"from app.services.retention_lifecycle import build_smart_insights; "
    "from app.services.email import send_payment_failed_email; print('retention_ok')\" 2>&1 | tail -10",
)
c.close()
print("done")
