#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1; "
    f"sleep 8; grep -n 'chrome-live\\|startLivePreview' {REMOTE}/frontend/src/components/redaction/plaidoirie-workspace.tsx | head -15; "
    f"curl -sf -o /dev/null -w 'web:%{{http_code}}\\n' https://lexhub.space/",
    timeout=90,
)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print(err[-500:])
c.close()
print("DONE")
