#!/usr/bin/env python3
"""Run pytest on VPS backend container."""
from __future__ import annotations

import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=40)
    _, o, e = client.exec_command(
        "docker exec sanad-backend-1 python -m pytest tests/ -q --tb=line 2>&1 | tail -40",
        timeout=180,
    )
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print(err)
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
