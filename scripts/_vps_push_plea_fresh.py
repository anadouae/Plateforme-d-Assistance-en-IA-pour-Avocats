#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/services/dictation.py",
    "backend/app/api/dictation.py",
    "backend/tests/test_dictation_pipeline.py",
    "frontend/src/lib/dictation-quality.ts",
    "frontend/src/lib/ownership.ts",
    "frontend/src/lib/plea-session.ts",
    "frontend/src/app/redaction/new/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/app/redaction/[templateId]/page.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/dashboard/dashboard-overview.tsx",
    "frontend/src/app/dashboard/page.tsx",
]


def run(c, cmd, timeout=180):
    print(">>", cmd[:220])
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
        "restart backend celery-worker 2>&1 | tail -20",
    )
    run(
        c,
        "sleep 3; curl -sS -m 15 -o /dev/null -w 'https:%{http_code}\\n' "
        "--resolve lexhub.space:443:127.0.0.1 https://lexhub.space/",
    )
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
