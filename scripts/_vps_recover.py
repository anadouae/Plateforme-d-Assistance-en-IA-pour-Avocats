#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=120):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out + err)[-4000:])
    print("exit", o.channel.recv_exit_status())


run("ps aux | grep -E 'docker (compose|build)|buildx' | grep -v grep | head -20")
run("docker builder prune -f")
run(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend celery-worker"
)
run("sleep 4; curl -sS -m 15 -o /dev/null -w 'https:%{http_code} t=%{time_total}\\n' --resolve lexhub.space:443:127.0.0.1 https://lexhub.space/")
run("free -h | head -3; df -h / | tail -1; uptime")
c.close()
