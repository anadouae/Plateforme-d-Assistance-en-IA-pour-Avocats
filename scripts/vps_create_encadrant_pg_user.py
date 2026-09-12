#!/usr/bin/env python3
"""Create a read-only PostgreSQL login for the PFA supervisor (DBeaver / pgAdmin)."""
from __future__ import annotations

import secrets
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
ROLE = "lexhub_encadrant"
PWD = "LhEnc" + secrets.token_hex(8)


def run(c, cmd, timeout=180):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-3000:])
    if err.strip():
        print("stderr:", err[-800:])
    print("exit", code)
    return code, out


def main() -> int:
    sql = f"""
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{ROLE}') THEN
    CREATE ROLE {ROLE} LOGIN PASSWORD '{PWD}';
  ELSE
    ALTER ROLE {ROLE} WITH LOGIN PASSWORD '{PWD}';
  END IF;
END$$;
GRANT CONNECT ON DATABASE sanad TO {ROLE};
GRANT USAGE ON SCHEMA public TO {ROLE};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO {ROLE};
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {ROLE};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {ROLE};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO {ROLE};
"""
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = c.open_sftp()
    remote_sql = f"{REMOTE}/.encadrant_readonly.sql"
    with sftp.file(remote_sql, "w") as f:
        f.write(sql)
    sftp.close()
    cmd = (
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U sanad -d sanad -v ON_ERROR_STOP=1 "
        f"< {remote_sql} && rm -f {remote_sql} && echo ROLE_OK"
    )
    code, out = run(c, cmd, 120)
    c.close()
    if code != 0 or "ROLE_OK" not in out:
        print("FAILED — do not share a partial password")
        return 1
    print("--- give this privately to the supervisor (not in the PDF) ---")
    print(f"user: {ROLE}")
    print(f"password: {PWD}")
    print("database: sanad")
    print("host after SSH tunnel: 127.0.0.1")
    print("port: 15432")
    print("rights: SELECT only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
