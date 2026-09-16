#!/usr/bin/env python3
from pathlib import Path
import paramiko
import time

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/billing/credit-spend-toast.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/settings/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    sftp.put(str(local), remote)
    # verify snippet
    with sftp.open(remote, "r") as f:
        data = f.read().decode("utf-8", errors="replace")
    ok = "let polishMsg" in data if "plaidoirie" in rel else True
    print("ok", rel, "bytes", local.stat().st_size, "polishMsg" if "plaidoirie" in rel else "", "FOUND" if ok else "MISSING")
sftp.close()

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart frontend 2>&1 | tail -15",
    timeout=180,
)
print(o.read().decode(errors="replace"))
time.sleep(14)
_, o, _ = c.exec_command(
    "curl -s -o /dev/null -w '%{http_code}' 'https://lexhub.space/redaction' ; echo ; "
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "logs frontend --tail 25 2>&1 | tail -25",
    timeout=90,
)
print(o.read().decode(errors="replace")[-2500:])
c.close()
