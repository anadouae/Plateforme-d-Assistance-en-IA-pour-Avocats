#!/usr/bin/env python3
import paramiko

FILES = [
    "backend/app/services/plaidoirie_prompt.py",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/lib/demo-plaidoirie.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/styles/sanad-ui.css",
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
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 | tail -8 && "
    f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -5",
    timeout=120,
)
print(o.read().decode(errors="replace")[-1200:])
print(e.read().decode(errors="replace")[-400:])
c.close()
print("done")
