#!/usr/bin/env python3
import paramiko

FILES = [
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/settings/team-panel.tsx",
]
REMOTE = "/opt/sanad"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1",
    timeout=60,
)
print(o.read().decode(errors="replace")[-600:])
c.close()
print("done")
