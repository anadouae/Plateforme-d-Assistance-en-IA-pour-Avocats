#!/usr/bin/env python3
"""Free VPS disk then rebuild backend/frontend with already-uploaded sources."""
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"


def run(c, cmd, timeout=600):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-5000:])
    if err.strip():
        print("stderr:", err[-2000:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

run(c, "df -h / | tail -2; docker system df")
run(c, "docker builder prune -af 2>&1 | tail -15", timeout=180)
run(c, "docker image prune -af 2>&1 | tail -15", timeout=180)
run(c, "journalctl --vacuum-size=50M 2>&1 | tail -5", timeout=60)
run(c, "df -h / | tail -1")

# Files already on disk via SFTP — rebuild without full pip if possible.
# Prefer recreate from existing compose context (COPY picks up SFTP files).
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate --build backend frontend 2>&1 | tail -60",
    timeout=900,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend python - <<'PY'\n"
    "from app.core.database import SessionLocal\n"
    "from app.services.billing import ensure_default_plans\n"
    "db = SessionLocal()\n"
    "ensure_default_plans(db)\n"
    "db.commit()\n"
    "print('plans synced')\n"
    "db.close()\n"
    "PY",
    timeout=120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "ps --format 'table {{.Name}}\\t{{.Status}}' 2>&1 | head -20",
)
c.close()
print("DONE")
