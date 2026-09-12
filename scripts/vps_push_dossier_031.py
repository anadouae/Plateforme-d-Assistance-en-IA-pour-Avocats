#!/usr/bin/env python3
"""Deploy dossier judiciaire vivant (031) + paiement MA env."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/alembic/versions/031_dossier_judiciaire_vivant.py",
    "backend/app/models/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/core/config.py",
    "backend/app/api/cases.py",
    "backend/app/api/documents.py",
    "backend/app/api/billing.py",
    "backend/app/api/workspace.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/services/billing.py",
    "backend/app/services/agenda_reminders.py",
    "backend/app/services/case_judicial.py",
    "backend/app/services/legal_citations.py",
    "backend/app/services/email.py",
    "backend/.env.example",
    "frontend/src/lib/case-judicial.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:220], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-4000:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP missing", rel, flush=True)
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
    f"exec -T backend alembic upgrade head 2>&1 | tail -40",
    180,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart backend frontend 2>&1 | tail -30",
    180,
)
time.sleep(14)
run(
    c,
    "curl -sS -o /dev/null -w 'home=%{http_code} api=%{http_code}\\n' "
    "https://lexhub.space/ https://lexhub.space/api/billing/payment-methods 2>&1 || "
    "curl -sS -o /dev/null -w 'home=%{http_code}\\n' https://lexhub.space/",
    40,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"logs backend --tail 40 2>&1 | tail -40",
    60,
)
c.close()
print("DONE", flush=True)
