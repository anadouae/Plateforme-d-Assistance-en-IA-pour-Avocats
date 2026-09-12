#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=90):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out or err)[-5000:])
    print("exit", o.channel.recv_exit_status())


run("curl -sS -m 15 -o /dev/null -w 'local3000:%{http_code} t=%{time_total}\\n' http://127.0.0.1:3000/")
run("curl -sS -m 15 -o /dev/null -w 'local8001:%{http_code} t=%{time_total}\\n' http://127.0.0.1:8001/api/health || curl -sS -m 15 -o /dev/null -w 'local8001:%{http_code}\\n' http://127.0.0.1:8001/docs")
run("curl -sS -m 20 -o /dev/null -w 'https:%{http_code} t=%{time_total}\\n' --resolve lexhub.space:443:127.0.0.1 https://lexhub.space/")
run("systemctl is-active caddy; journalctl -u caddy --no-pager -n 30")
run("docker logs sanad-frontend-1 --tail 40 2>&1")
run("docker logs sanad-backend-1 --tail 25 2>&1")
run("docker system df; ls /tmp | head; docker ps --filter status=exited")
c.close()
