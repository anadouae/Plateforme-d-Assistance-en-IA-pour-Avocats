#!/usr/bin/env python3
"""Deploy LexHub rebrand + auth/email fixes to production VPS."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    # Backend
    "backend/app/core/config.py",
    "backend/app/main.py",
    "backend/app/services/email.py",
    "backend/app/api/admin.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/email.py",
    "frontend/src/lib/api.ts",
    "frontend/src/app/magic-login/page.tsx",
    "frontend/src/app/confirm-email/page.tsx",
    "frontend/src/app/verify-email/page.tsx",
    "frontend/src/app/templates/page.tsx",
    "frontend/src/app/activate/page.tsx",
    "frontend/src/components/brand/sanad-page-loader.tsx",
    # Frontend — rebrand + auth + admin
    "frontend/src/store/locale.ts",
    "frontend/src/app/layout.tsx",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/roles.ts",
    "frontend/src/app/join/pending/page.tsx",
    "frontend/src/app/admin/page.tsx",
    "frontend/src/app/admin/cabinets/page.tsx",
    "frontend/src/app/confidentialite/page.tsx",
    "frontend/src/app/mentions-legales/page.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/export-pdf.ts",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/components/brand/sanad-logo.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/auth/legal-doc-link.tsx",
    "frontend/src/components/auth/password-rules-list.tsx",
    "frontend/src/lib/register-draft.ts",
    "frontend/src/lib/legal-content.ts",
    "frontend/src/app/forgot-password/page.tsx",
    "frontend/src/app/reset-password/page.tsx",
    "frontend/src/components/auth/auth-layout.tsx",
    "frontend/src/components/auth/auth-product-demo.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/components/layout/public-footer.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/user-account-menu.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
]


def ssh_run(client: paramiko.SSHClient, cmd: str) -> str:
    _, out, err = client.exec_command(cmd, timeout=240)
    code = out.channel.recv_exit_status()
    text = out.read().decode(errors="replace") + err.read().decode(errors="replace")
    if code != 0:
        raise RuntimeError(f"cmd failed ({code}): {cmd}\n{text}")
    return text


def main() -> int:
    missing = [f for f in FILES if not (ROOT / f).is_file()]
    if missing:
        print("Missing:", *missing, sep="\n  ", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=40)

    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"{REMOTE}/{rel}"
        ssh_run(client, f"mkdir -p $(dirname {remote})")
        sftp.put(str(local), remote)
        print("uploaded", rel)
    sftp.close()

    print("recreating backend + frontend...")
    out = ssh_run(
        client,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1",
    )
    print(out[-2500:])

    time.sleep(10)
    health = ssh_run(
        client,
        "docker exec sanad-backend-1 curl -s http://127.0.0.1:8000/api/health 2>/dev/null | head -c 500",
    )
    print("health:", health)
    client.close()
    print("DONE — https://lexhub.space")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        raise SystemExit(1)
