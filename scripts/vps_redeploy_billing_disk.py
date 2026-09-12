#!/usr/bin/env python3
"""Free disk + redeploy billing after failed frontend build."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

EXTRA = [
    "backend/app/main.py",
]


def run(c, cmd, timeout=600):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4500:])
    if err.strip():
        print("stderr:", err[-1500:])
    print("exit", code)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)

run(c, "df -h / && docker system df")
run(c, "docker builder prune -af 2>&1 | tail -8", timeout=300)
run(c, "docker image prune -af 2>&1 | tail -10", timeout=300)
run(c, "df -h /")

sftp = c.open_sftp()
for rel in EXTRA:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend alembic upgrade head 2>&1 | tail -20",
    timeout=120,
)
run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate --build backend frontend 2>&1 | tail -50",
    timeout=900,
)
run(c, "curl -fsS -o /dev/null -w '%{http_code}' https://lexhub.space/tarifs")
run(c, "curl -fsS -o /dev/null -w '%{http_code}' https://lexhub.space/api/billing/plans")
c.close()
print("done")
