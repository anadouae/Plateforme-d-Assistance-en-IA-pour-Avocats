#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=180):
    print(">>", cmd[:280])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print((out + err)[-4000:])
    print("exit", o.channel.recv_exit_status())


run("ls -ld /var/lib/docker/overlay2; du -sh /var/lib/docker/overlay2 2>&1 | tail -3")
run("docker buildx prune -af 2>&1 | tail -20")
run("du -sh /var/lib/docker/volumes/sanad_hf_cache/_data 2>/dev/null; ls /var/lib/docker/volumes/sanad_hf_cache/_data 2>/dev/null | head -20")
run("df -h /")
c.close()
