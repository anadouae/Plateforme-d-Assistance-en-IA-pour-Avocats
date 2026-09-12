#!/usr/bin/env python3
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/core/config.py",
    "backend/app/api/billing.py",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/settings/billing-panel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

def run(cmd, t=300):
    print(">>", cmd[:180])
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out or err)[-3000:])
    return o.channel.recv_exit_status()

run(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -20"
)
time.sleep(14)
run(
    "curl -sS https://lexhub.space/api/billing/plans | python3 -c "
    "'import sys,json; d=json.load(sys.stdin); "
    "print([(p[\"slug\"], p[\"price_mad_monthly\"], p[\"trial_days\"], len(p.get(\"highlights\") or [])) for p in d])'"
)
c.close()
print("done")
