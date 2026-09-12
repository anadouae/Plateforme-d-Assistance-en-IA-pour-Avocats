#!/usr/bin/env python3
"""Run backend tests + smoke health on VPS."""
from __future__ import annotations

import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=45)

    cmds = [
        "docker exec sanad-backend-1 python -m pytest tests/ -q --tb=line 2>&1 | tail -40",
        "curl -s https://lexhub.space/api/health | head -c 350",
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/login",
        "curl -s -o /dev/null -w '%{http_code}' https://lexhub.space/admin",
    ]
    for cmd in cmds:
        print("===", cmd[:70], "===")
        _, out, err = client.exec_command(cmd, timeout=180)
        print(out.read().decode(errors="replace"))
        e = err.read().decode(errors="replace").strip()
        if e:
            print("ERR:", e[:300])
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
