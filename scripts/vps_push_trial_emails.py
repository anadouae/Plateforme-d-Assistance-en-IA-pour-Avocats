#!/usr/bin/env python3
"""Deploy trial lifecycle emails + commercial UX + celery beat."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/email.py",
    "backend/app/services/trial_lifecycle.py",
    "backend/app/services/billing.py",
    "backend/app/services/celery_app.py",
    "backend/app/services/tasks.py",
    "backend/app/api/auth.py",
    "backend/app/api/billing.py",
    "backend/app/api/team.py",
    "frontend/src/components/billing/subscription-banner.tsx",
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
        print(text[-5000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

run(c, "docker builder prune -af 2>&1 | tail -3; df -h / | tail -1", timeout=180)

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
    f"up -d --force-recreate backend frontend celery-worker celery-beat 2>&1 | tail -40",
    timeout=360,
)
run(
    c,
    "sleep 12; curl -sS -o /dev/null -w 'home=%{http_code} tarifs=%{http_code}\\n' "
    "https://lexhub.space/ https://lexhub.space/tarifs; "
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "logs --tail=15 celery-beat 2>&1 | tail -20",
)
c.close()
print("done")
