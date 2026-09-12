#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
rel = "frontend/src/components/redaction/plaidoirie-workspace.tsx"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
sftp.close()
print("uploaded", rel)
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1; "
    f"sleep 6; grep -n 'chromeOnly\\|Fichier audio\\|handleAudioFile\\|Mode Chrome' {REMOTE}/{rel} | head -20; "
    f"curl -sf -o /dev/null -w 'web:%{{http_code}}\\n' https://lexhub.space/",
    timeout=90,
)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print(err[-400:])
c.close()
print("DONE")
