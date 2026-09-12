#!/usr/bin/env python3
"""Deploy plaidoirie UX 1B/2A/3C + rédaction pro + export PDF/Word."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/plaidoirie_prompt.py",
    "backend/app/services/plaidoirie_case_compose.py",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/pdf_export.py",
    "backend/app/services/docx_export.py",
    "backend/app/api/plaidoirie_templates.py",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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

_, o, _ = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -30",
    timeout=600,
)
print(o.read().decode(errors="replace")[-4000:])
c.close()
print("done")
