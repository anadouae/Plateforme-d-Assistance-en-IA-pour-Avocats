#!/usr/bin/env python3
"""Deploy hybrid trial usage caps."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/billing.py",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/billing-plans-fallback.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -25
sleep 6
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "
from app.services.billing import TRIAL_USAGE_CAPS, apply_trial_cap
print('solo trial credits', apply_trial_cap('solo','ai_credits',600,in_trial=True))
print('solo paid credits', apply_trial_cap('solo','ai_credits',600,in_trial=False))
print('pro trial pleas', apply_trial_cap('pro','plaidoiries',120,in_trial=True))
print('ent trial credits', apply_trial_cap('enterprise','ai_credits',5000,in_trial=True))
print('caps keys', sorted(TRIAL_USAGE_CAPS))
"
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace")[-5000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-1500:])
c.close()
print("done")
