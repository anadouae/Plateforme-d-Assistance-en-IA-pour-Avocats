#!/usr/bin/env python3
"""Hot-patch billing-panel.tsx syntax fix to VPS."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
REL = "frontend/src/components/settings/billing-panel.tsx"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
local = ROOT / REL
remote = f"{REMOTE}/{REL}"
sftp.put(str(local), remote)
print("sftp", REL)
sftp.close()

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart frontend 2>&1 | tail -30",
    timeout=180,
)
print(o.read().decode(errors="replace")[-3000:])
print(e.read().decode(errors="replace")[-1000:])
print("exit", o.channel.recv_exit_status())

_, o2, _ = c.exec_command(
    "sleep 8; curl -sS -o /dev/null -w 'home:%{http_code}\\nsettings:%{http_code}\\n' "
    "https://lexhub.space/ https://lexhub.space/settings"
)
print(o2.read().decode(errors="replace"))
c.close()
print("DONE")
