#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "frontend/src/store/auth.ts",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/cases/field-coach.tsx",
    "frontend/src/lib/case-field-coach.ts",
]


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=50, banner_timeout=80)
    sftp = c.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"{REMOTE}/{rel}"
        parent = str(Path(remote).parent).replace("\\", "/")
        _, o, _ = c.exec_command(f"mkdir -p {parent}")
        o.channel.recv_exit_status()
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()
    _, o, e = c.exec_command(
        "curl -sS -m 15 -o /dev/null -w 'https:%{http_code}\\n' "
        "--resolve lexhub.space:443:127.0.0.1 https://lexhub.space/login"
    )
    print(o.read().decode() + e.read().decode())
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
