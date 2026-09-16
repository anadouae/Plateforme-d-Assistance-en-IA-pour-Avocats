#!/usr/bin/env python3
"""Deploy dock fix + admin LexHub brand + Aide/About."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/components/layout/user-account-menu.tsx",
    "frontend/src/app/aide/page.tsx",
    "frontend/src/app/about/page.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP missing", rel)
        continue
    sftp.put(str(local), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -12
sleep 20
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'aide:%{http_code}\n' https://lexhub.space/aide || true
curl -sf -o /dev/null -w 'about:%{http_code}\n' https://lexhub.space/about || true
curl -sf -o /dev/null -w 'admin:%{http_code}\n' https://lexhub.space/admin || true
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
