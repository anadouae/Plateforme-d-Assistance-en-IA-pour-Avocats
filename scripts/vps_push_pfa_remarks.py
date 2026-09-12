#!/usr/bin/env python3
"""Push dictation/report-aligned product fixes to lexhub VPS."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/dictation_contradictions.py",
    "backend/app/services/dictation.py",
    "backend/app/services/referral.py",
    "backend/app/api/team.py",
    "docker-compose.lexhub.yml",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/i18n/translations.ts",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/app/join/page.tsx",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:200])
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


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = c.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            raise SystemExit(f"missing {rel}")
        remote = f"{REMOTE}/{rel}"
        parent = str(Path(remote).parent).replace("\\", "/")
        _, o, _ = c.exec_command(f"mkdir -p {parent}")
        o.channel.recv_exit_status()
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "up -d postgres redis minio backend frontend celery-worker 2>&1 | tail -50",
        timeout=600,
    )
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart backend frontend celery-worker 2>&1 | tail -20",
        timeout=180,
    )
    run(
        c,
        "sleep 12 && curl -fsS -o /dev/null -w '%{http_code}' https://lexhub.space/",
        timeout=120,
    )
    c.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
