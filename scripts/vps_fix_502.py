#!/usr/bin/env python3
import time
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for i in range(8):
    try:
        c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
        break
    except Exception as e:
        print("retry", i, e)
        time.sleep(6)
else:
    raise SystemExit("ssh fail")

t = c.get_transport()
if t:
    t.set_keepalive(20)

cmds = [
    "uptime; free -h | head -3",
    "docker ps -a --format '{{.Names}} {{.Status}}' | grep sanad",
    "docker logs --tail 40 sanad-frontend-1 2>&1",
    "docker logs --tail 40 sanad-backend-1 2>&1",
    "curl -sS -o /dev/null -w 'fe:%{http_code} ' http://127.0.0.1:3000/ ; curl -sS -o /dev/null -w 'be:%{http_code}\\n' http://127.0.0.1:8001/api/health",
    "systemctl is-active caddy 2>/dev/null; journalctl -u caddy --no-pager -n 15 2>/dev/null | tail -15",
]
for cmd in cmds:
    print("\n$", cmd[:80])
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode(errors="replace")[-2500:])
    err = e.read().decode(errors="replace")
    if err:
        print(err[-500:])

c.close()
