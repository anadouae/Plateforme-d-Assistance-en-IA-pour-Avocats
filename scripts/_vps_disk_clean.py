#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=300):
    print(">>", cmd[:300])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out + err)[-6000:])
    print("exit", o.channel.recv_exit_status())


run("du -sh /var/lib/docker/overlay2 /var/lib/docker/image /var/lib/docker/buildkit /var/lib/docker/volumes 2>/dev/null")
run("docker volume ls -f dangling=true")
run("docker builder prune -af")
run("docker image prune -f")
run("docker volume rm b33a480cbe137e583a4497151030bdfe540429194dd593a4ceaafedd2bd03b5a 2>&1 || true")
run("df -h /")
run("docker system df")
run("curl -sS -m 15 -o /dev/null -w 'https:%{http_code}\\n' --resolve lexhub.space:443:127.0.0.1 https://lexhub.space/")
c.close()
