#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/app/admin/logs/page.tsx",
    "frontend/src/components/layout/user-account-menu.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/components/ai/document-status-badge.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/components/billing/referral-nudge-modal.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "backend/app/api/admin.py",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"/opt/sanad/{rel}"
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    "cd /opt/sanad; docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps restart frontend backend 2>&1 | tail -10; sleep 16; curl -sf -o /dev/null -w 'admin:%{http_code}\\n' https://lexhub.space/admin",
    timeout=140,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
