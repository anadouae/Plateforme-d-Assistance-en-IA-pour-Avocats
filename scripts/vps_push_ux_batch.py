#!/usr/bin/env python3
"""Deploy UX batch: login i18n, plaidoirie export/save, case edit, role label."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/auth.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/docx_export.py",
    "backend/app/services/pdf_export.py",
    "backend/app/services/arabic_text_fix.py",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/i18n/labels.ts",
    "frontend/src/styles/sanad-ui.css",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:180])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("stderr:", err[-1500:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing local file: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -40",
    timeout=600,
)
run(
    c,
    f"cd {REMOTE} && sleep 10 && curl -fsS -o /dev/null -w '%{{http_code}}' https://lexhub.space/ 2>&1",
    timeout=120,
)
c.close()
print("done")
