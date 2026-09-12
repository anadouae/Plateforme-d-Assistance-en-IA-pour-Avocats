#!/usr/bin/env python3
"""Free disk + hot-deploy quiet dictation UI without full backend rebuild."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "backend/app/services/dictation.py",
    "docker-compose.lexhub.yml",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)


def run(cmd: str, timeout: int = 300) -> str:
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print(out)
    if err.strip():
        print("ERR", err[-800:])
    return out


print("=== disk before ===")
run("df -h /; docker system df")

print("=== prune ===")
run(
    "docker builder prune -af 2>&1 | tail -8; "
    "docker image prune -af 2>&1 | tail -10; "
    "docker container prune -f 2>&1 | tail -5; "
    "df -h /"
)

sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
set -e
cd /opt/sanad
grep -q '^DICTATION_POLISH_USE_LLM=' .env.vps 2>/dev/null \
  && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' .env.vps \
  || echo 'DICTATION_POLISH_USE_LLM=true' >> .env.vps
grep -q '^DICTATION_POLISH_USE_LLM=' .env 2>/dev/null \
  && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' .env \
  || echo 'DICTATION_POLISH_USE_LLM=true' >> .env

BE=$(docker ps --format '{{.Names}}' | grep -E 'backend' | head -1)
FE=$(docker ps --format '{{.Names}}' | grep -E 'frontend' | head -1)
echo "BE=$BE FE=$FE"

docker cp frontend/src/components/redaction/plaidoirie-workspace.tsx \
  "$FE:/app/src/components/redaction/plaidoirie-workspace.tsx" || \
docker cp frontend/src/components/redaction/plaidoirie-workspace.tsx \
  "$FE:/frontend/src/components/redaction/plaidoirie-workspace.tsx" || true

docker cp backend/app/services/dictation.py "$BE:/app/app/services/dictation.py"

# Recreate backend for env (no image rebuild)
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --no-build --force-recreate backend 2>&1 | tail -20

# Frontend: try slim rebuild; if fail, restart + hope volume
FREE=$(df / | awk 'NR==2{print $4}')
echo "free_kb=$FREE"
if [ "$FREE" -gt 2000000 ]; then
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --build --no-deps frontend 2>&1 | tail -40
else
  echo "low space — restart frontend"
  docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -10
fi

sleep 15
BE2=$(docker ps --format '{{.Names}}' | grep -E 'backend' | head -1)
docker exec "$BE2" printenv DICTATION_POLISH_USE_LLM
docker exec "$BE2" python -c "from app.services.dictation import POLISH_SYSTEM_AR_AUDIO; print('prompt_ok', 'همزات' in POLISH_SYSTEM_AR_AUDIO)"
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
df -h /
"""
run(cmd, timeout=600)
c.close()
print("DONE")
