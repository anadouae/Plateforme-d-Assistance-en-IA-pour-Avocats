#!/usr/bin/env python3
"""Diagnose and recover Next.js ChunkLoadError on lexhub."""
import time
import urllib.request
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
t = c.get_transport()
if t:
    t.set_keepalive(20)

print("=== before ===")
_, o, _ = c.exec_command(
    "docker ps --filter name=sanad-frontend --format '{{.Names}} {{.Status}}'; "
    "free -h | head -2; "
    "docker logs --tail 40 sanad-frontend-1 2>&1"
)
print(o.read().decode(errors="replace")[-2500:])

print("=== recreate frontend (clear .next cache) ===")
_, o, e = c.exec_command(
    "rm -rf /opt/sanad/frontend/.next; "
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "up -d --force-recreate frontend 2>&1",
    timeout=120,
)
print(o.read().decode(errors="replace")[-1500:])
print(e.read().decode(errors="replace")[-400:])

ok = False
for i in range(30):
    time.sleep(6)
    _, o2, _ = c.exec_command(
        "docker inspect -f '{{.State.Status}} {{.State.Restarting}}' sanad-frontend-1; "
        "curl -sS -o /tmp/lexhub-login.html -w '%{http_code} %{time_total}' "
        "--max-time 25 http://127.0.0.1:3000/login 2>/dev/null || echo '000 0'; "
        "echo; docker logs --tail 8 sanad-frontend-1 2>&1 | tail -8"
    )
    out = o2.read().decode(errors="replace")
    print(f"--- poll {i+1} ---")
    print(out[-700:])
    first = out.splitlines()[0] if out.splitlines() else ""
    if "running false" in first and "200 " in out:
        ok = True
        break

print("local_ok", ok)
c.close()

try:
    req = urllib.request.Request("https://lexhub.space/login", headers={"Cache-Control": "no-cache"})
    r = urllib.request.urlopen(req, timeout=40)
    print("public", r.status, len(r.read()))
except Exception as exc:
    print("public ERR", exc)
