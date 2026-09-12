#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=180):
    print(">>", cmd[:300])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out + err)[-8000:])
    print("exit", o.channel.recv_exit_status())


run("df -h /")
run("du -xh --max-depth=1 / 2>/dev/null | sort -hr | head -20")
run("du -xh --max-depth=1 /var 2>/dev/null | sort -hr | head -15")
run("du -xh --max-depth=1 /opt 2>/dev/null | sort -hr | head -15")
run("du -xh --max-depth=1 /opt/sanad 2>/dev/null | sort -hr | head -20")
run("du -xh --max-depth=1 /var/lib/docker 2>/dev/null | sort -hr | head -20")
run("docker system df -v 2>/dev/null | head -80")
run("journalctl --disk-usage")
run("du -sh /var/log /var/lib/docker /opt/sanad /root /tmp 2>/dev/null")
c.close()
