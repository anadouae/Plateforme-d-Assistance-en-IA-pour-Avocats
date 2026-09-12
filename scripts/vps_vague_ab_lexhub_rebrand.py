#!/usr/bin/env python3
"""
Vague A + B (prod) :
- Couper Adminer HTTPS public (Caddy)
- Rotation mot de passe Postgres
- Renommer rôle + base sanad → lexhub
- Symlink /opt/lexhub
- Push fichiers compose / app critiques
- Migrer e-mails démo @sanad.ma → @lexhub.space
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
SSH_PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

NEW_DB_PASS = "LhPg-" + secrets.token_urlsafe(18)


def run(c: paramiko.SSHClient, cmd: str, timeout: int = 300) -> tuple[int, str, str]:
    print(">>", cmd[:240].replace(NEW_DB_PASS, "***"))
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-2500:])
    if err.strip():
        print("stderr:", err[-600:])
    print("exit", code)
    return code, out, err


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=SSH_PASSWORD, timeout=60, banner_timeout=120)
    sftp = c.open_sftp()

    files = [
        "deploy/Caddyfile.lexhub",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "docker-compose.lexhub.yml",
        "backend/app/core/config.py",
        "backend/app/services/web_search.py",
        "backend/scripts/seed_test_accounts.py",
        "frontend/src/components/layout/app-shell.tsx",
        "frontend/src/components/auth/unified-auth.tsx",
        "frontend/src/app/dashboard/loading.tsx",
        "frontend/src/app/home/page.tsx",
        "frontend/src/app/cases/[id]/page.tsx",
        "frontend/tailwind.config.ts",
        "README.md",
        "docs/ADMINER_ACCES.md",
        "docs/COMPTES_ET_TESTS.md",
    ]
    for rel in files:
        local = ROOT / rel
        if not local.is_file():
            print("skip missing", rel)
            continue
        remote = f"{REMOTE}/{rel}"
        # ensure remote dir
        remote_dir = str(Path(remote).parent).replace("\\", "/")
        run(c, f"mkdir -p {remote_dir}", 30)
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()

    # 1) Caddy without public Adminer
    run(
        c,
        "cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile && "
        "caddy validate --config /etc/caddy/Caddyfile && "
        "systemctl reload caddy || caddy reload --config /etc/caddy/Caddyfile",
        90,
    )

    # 2) Stop app writers, rename DB + role, set password
    sql = f"""
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname IN ('sanad','lexhub') AND pid <> pg_backend_pid();

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'sanad')
     AND NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'lexhub') THEN
    ALTER DATABASE sanad RENAME TO lexhub;
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sanad')
     AND NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lexhub') THEN
    ALTER ROLE sanad RENAME TO lexhub;
  END IF;
END$$;

ALTER ROLE lexhub WITH LOGIN PASSWORD '{NEW_DB_PASS}';
GRANT ALL PRIVILEGES ON DATABASE lexhub TO lexhub;
"""
    # write sql remotely without echoing password in process list too much
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.lexhub_rename.sql", "w") as f:
        f.write(sql)
    sftp.close()

    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"stop backend celery celery-beat frontend 2>&1 | tail -20",
        120,
    )
    # Use current superuser inside container (still sanad or lexhub)
    code, out, _ = run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres sh -c \"psql -U sanad -d postgres -v ON_ERROR_STOP=1 < /dev/stdin\" "
        f"< {REMOTE}/.lexhub_rename.sql 2>&1 || "
        f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres sh -c \"psql -U lexhub -d postgres -v ON_ERROR_STOP=1 < /dev/stdin\" "
        f"< {REMOTE}/.lexhub_rename.sql 2>&1",
        120,
    )

    # 3) Patch .env.vps DATABASE_URL + POSTGRES_*
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
p.write_text(t, encoding="utf-8")
print("ENV_OK")
"""
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.patch_env_lexhub.py", "w") as f:
        f.write(helper)
    sftp.close()
    run(c, f"python3 {REMOTE}/.patch_env_lexhub.py && rm -f {REMOTE}/.patch_env_lexhub.py", 30)

    run(c, f"rm -f {REMOTE}/.lexhub_rename.sql", 20)

    # 4) Symlink brand path
    run(c, "ln -sfn /opt/sanad /opt/lexhub && ls -la /opt/lexhub | head -3", 30)

    # 5) Recreate/restart stack with new env
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"--env-file .env.vps up -d postgres 2>&1 | tail -15",
        120,
    )
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"--env-file .env.vps up -d backend celery celery-beat frontend adminer 2>&1 | tail -25",
        180,
    )

    # 6) Migrate demo emails + passwords inside DB
    migrate_users = r"""
UPDATE users SET email = 'demo@lexhub.space' WHERE email = 'demo@sanad.ma';
UPDATE users SET email = 'avocat@lexhub.space' WHERE email = 'avocat@sanad.ma';
UPDATE users SET email = 'assistant@lexhub.space' WHERE email = 'assistant@sanad.ma';
"""
    sftp = c.open_sftp()
    with sftp.file(f"{REMOTE}/.migrate_emails.sql", "w") as f:
        f.write(migrate_users)
    sftp.close()
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U lexhub -d lexhub -v ON_ERROR_STOP=1 < {REMOTE}/.migrate_emails.sql "
        f"&& rm -f {REMOTE}/.migrate_emails.sql",
        60,
    )

    # Reset demo passwords via backend (hash)
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T backend python scripts/seed_test_accounts.py 2>&1 | tail -40",
        120,
    )

    # 7) Verify
    run(
        c,
        "curl -s -o /dev/null -w 'site:%{http_code}\\n' https://lexhub.space/ ; "
        "curl -s -o /dev/null -w 'adminer_public:%{http_code}\\n' https://lexhub.space/_ops/db/ ; "
        "curl -s -o /dev/null -w 'adminer_local:%{http_code}\\n' http://127.0.0.1:8088/ ; "
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"exec -T postgres psql -U lexhub -d lexhub -c \"SELECT current_database(), current_user;\" ",
        90,
    )

    c.close()

    cred = Path.home() / "Desktop" / "LexHub_DB_credentials.txt"
    cred.write_text(
        f"""LexHub — credentials base (PROD) — confidentiel

Base PostgreSQL (après Vague B):
  host (tunnel): 127.0.0.1
  port: 15432
  database: lexhub
  user: lexhub
  password: {NEW_DB_PASS}

Adminer (tunnel only):
  python scripts\\open_adminer_tunnel.py
  http://127.0.0.1:8088
  serveur: postgres

Comptes app démo:
  demo@lexhub.space / LexHub2026!
  avocat@lexhub.space / LexHub2026!
  assistant@lexhub.space / LexHub2026!

Adminer n'est PLUS sur https://lexhub.space/_ops/db/
Chemin code: /opt/sanad (symlink /opt/lexhub)
""",
        encoding="utf-8",
    )
    print("CREDENTIALS ->", cred)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
