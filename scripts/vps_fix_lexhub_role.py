#!/usr/bin/env python3
"""Fix Vague B: create lexhub role, point DATABASE_URL, restart stack, migrate emails."""
from __future__ import annotations

import re
import secrets
from pathlib import Path

import paramiko

HOST = "51.38.78.23"
SSH_PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
NEW_DB_PASS = "LhPg-" + secrets.token_urlsafe(18)


def run(c, cmd, timeout=300):
    print(">>", cmd[:220].replace(NEW_DB_PASS, "***"))
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-2000:])
    if err.strip():
        print("stderr:", err[-500:])
    print("exit", code)
    return code, out, err


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=SSH_PASSWORD, timeout=60, banner_timeout=120)

    sql = f"""
-- Ensure DB name
SELECT datname FROM pg_database WHERE datname IN ('sanad','lexhub');

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lexhub') THEN
    CREATE ROLE lexhub LOGIN SUPERUSER PASSWORD '{NEW_DB_PASS}';
  ELSE
    ALTER ROLE lexhub WITH LOGIN SUPERUSER PASSWORD '{NEW_DB_PASS}';
  END IF;
END$$;

-- Keep legacy role usable but rotate its password too
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sanad') THEN
    ALTER ROLE sanad WITH PASSWORD '{NEW_DB_PASS}';
  END IF;
END$$;

ALTER DATABASE lexhub OWNER TO lexhub;
GRANT ALL PRIVILEGES ON DATABASE lexhub TO lexhub;
"""
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.fix_lexhub_role.sql", "w") as f:
        f.write(sql)
    sftp.close()

    # Connect as current bootstrap user `sanad` to database postgres or lexhub
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U sanad -d postgres -v ON_ERROR_STOP=1 < {REMOTE}/.fix_lexhub_role.sql",
        90,
    )

    # Patch env to use lexhub user + new password + lexhub db
    helper = f"""#!/usr/bin/env python3
from pathlib import Path
import re
p = Path("/opt/sanad/.env.vps")
t = p.read_text(encoding="utf-8", errors="replace")
pwd = {NEW_DB_PASS!r}
url = "postgresql://lexhub:" + pwd + "@postgres:5432/lexhub"
if re.search(r"^DATABASE_URL=", t, re.M):
    t = re.sub(r"^DATABASE_URL=.*$", "DATABASE_URL=" + url, t, flags=re.M)
else:
    t += "\\nDATABASE_URL=" + url + "\\n"
for k, v in {{"POSTGRES_USER": "lexhub", "POSTGRES_DB": "lexhub", "POSTGRES_PASSWORD": pwd}}.items():
    if re.search(r"^" + k + r"=", t, re.M):
        t = re.sub(r"^" + k + r"=.*$", k + "=" + v, t, flags=re.M)
    else:
        t += "\\n" + k + "=" + v + "\\n"
# scrub old sanad URL fragments if any
t = t.replace("@postgres:5432/sanad", "@postgres:5432/lexhub")
p.write_text(t, encoding="utf-8")
print("ENV_OK")
"""
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.patch_env2.py", "w") as f:
        f.write(helper)
    sftp.close()
    run(c, f"python3 {REMOTE}/.patch_env2.py && rm -f {REMOTE}/.patch_env2.py {REMOTE}/.fix_lexhub_role.sql", 30)

    # Restart app services (correct celery service names)
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps "
        f"up -d backend celery-worker celery-beat frontend adminer 2>&1 | tail -30",
        180,
    )
    # fallback names
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps "
        f"ps --services 2>&1 | head -40",
        60,
    )

    emails = """
UPDATE users SET email = 'demo@lexhub.space' WHERE email IN ('demo@sanad.ma','demo@lexhub.space');
UPDATE users SET email = 'avocat@lexhub.space' WHERE email IN ('avocat@sanad.ma','avocat@lexhub.space');
UPDATE users SET email = 'assistant@lexhub.space' WHERE email IN ('assistant@sanad.ma','assistant@lexhub.space');
"""
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.emails.sql", "w") as f:
        f.write(emails)
    sftp.close()
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U lexhub -d lexhub -v ON_ERROR_STOP=1 < {REMOTE}/.emails.sql && rm -f {REMOTE}/.emails.sql",
        60,
    )

    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T backend python scripts/seed_test_accounts.py 2>&1 | tail -30",
        120,
    )

    run(
        c,
        "curl -s -o /dev/null -w 'site:%{http_code}\\n' https://lexhub.space/ ; "
        "curl -s -o /dev/null -w 'api_health:%{http_code}\\n' https://lexhub.space/health ; "
        "curl -s -o /dev/null -w 'ops_db:%{http_code}\\n' https://lexhub.space/_ops/db/ ; "
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U lexhub -d lexhub -c \"SELECT current_database(), current_user; SELECT email FROM users WHERE email LIKE '%lexhub%' OR email LIKE '%sanad%' ORDER BY 1;\"",
        90,
    )

    c.close()
    cred = Path.home() / "Desktop" / "LexHub_DB_credentials.txt"
    cred.write_text(
        f"""LexHub — credentials base (PROD) — confidentiel

PostgreSQL:
  database: lexhub
  user: lexhub
  password: {NEW_DB_PASS}
  port tunnel: 15432 → 127.0.0.1

Adminer: tunnel only → http://127.0.0.1:8088
  serveur: postgres

Comptes app:
  demo@lexhub.space / LexHub2026!
  avocat@lexhub.space / LexHub2026!
  assistant@lexhub.space / LexHub2026!

/_ops/db public: DISABLED
Symlink: /opt/lexhub → /opt/sanad
""",
        encoding="utf-8",
    )
    print("CREDENTIALS ->", cred)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
