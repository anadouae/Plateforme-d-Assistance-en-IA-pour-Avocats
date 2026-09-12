#!/usr/bin/env python3
"""Deploy daily-cap choice (continue / wait) + related UI. No --build."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/core/rate_limit.py",
    "backend/app/services/billing.py",
    "backend/app/api/cases.py",
    "backend/app/api/billing.py",
    "backend/app/api/dictation.py",
    "backend/app/api/documents.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/credit-spend-toast.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
set -e
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -20
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.core.rate_limit import check_cabinet_ai_daily; from app.services.billing import begin_ai_action; import inspect; assert 'acknowledge_overage' in inspect.signature(check_cabinet_ai_daily).parameters; assert 'request' in inspect.signature(begin_ai_action).parameters; print('ok daily choice')"
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-6000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-1500:])
c.close()
print("done")
