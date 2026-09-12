#!/usr/bin/env python3
"""Push UI fixes to lexhub VPS. Requires VPS_SSH_PASSWORD."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")

FILES = [
    "frontend/src/app/cases/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/dashboard/loading.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/case-domains.ts",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/lib/i18n/labels.ts",
    "frontend/src/lib/export-official-doc.ts",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/store/locale.ts",
    "frontend/src/store/auth.ts",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/providers/locale-provider.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/language-switch.tsx",
    "frontend/src/components/brand/sanad-logo.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/auth/auth-product-demo.tsx",
    "frontend/src/store/auth.ts",
    "frontend/src/components/onboarding/sanad-onboarding.tsx",
    "frontend/src/hooks/use-onboarding.ts",
    "frontend/src/lib/onboarding-steps.ts",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/plea-step-carousel.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
]


def main() -> int:
    if not PASSWORD:
        print("Set VPS_SSH_PASSWORD then rerun.", file=sys.stderr)
        return 1

    missing = [f for f in FILES if not (ROOT / f).is_file()]
    if missing:
        print("Missing files:", *missing, sep="\n  ", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST} …")
    client.connect(
        HOST,
        username=USER,
        password=PASSWORD,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"/opt/sanad/{rel.replace(chr(92), '/')}"
        # ensure remote dir exists
        remote_dir = remote.rsplit("/", 1)[0]
        try:
            sftp.stat(remote_dir)
        except OSError:
            parts = remote_dir.split("/")
            cur = ""
            for p in parts:
                if not p:
                    continue
                cur += f"/{p}"
                try:
                    sftp.stat(cur)
                except OSError:
                    sftp.mkdir(cur)
        print("upload", rel)
        sftp.put(str(local), remote)
    sftp.close()

    cmd = (
        "cd /opt/sanad && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T frontend sh -lc 'rm -rf /app/.next' && "
        "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart frontend"
    )
    print("restart frontend …")
    _, stdout, stderr = client.exec_command(cmd, timeout=180)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if out.strip():
        print(out.strip()[-2000:])
    if err.strip():
        print(err.strip()[-1500:], file=sys.stderr)
    client.close()
    print("done" if code == 0 else f"exit={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
