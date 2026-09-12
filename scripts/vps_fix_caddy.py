#!/usr/bin/env python3
"""Verify/fix Caddy config on VPS after security headers deploy."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)

cmds = [
    "cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile",
    "caddy validate --config /etc/caddy/Caddyfile 2>&1",
    "systemctl restart caddy 2>&1; sleep 1; systemctl is-active caddy 2>&1",
    "curl -sI https://lexhub.space/ | head -25",
    "curl -sI https://lexhub.space/_next/static/ 2>&1 | head -15 || true",
]
for cmd in cmds:
    print(">>>", cmd[:80])
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print("err:", err[-800:])
c.close()
