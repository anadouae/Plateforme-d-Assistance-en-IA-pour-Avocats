#!/usr/bin/env python3
"""Install daily LexHub backups on the VPS (cron 02:30) and run one backup now."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"


def run(c, cmd, timeout=300):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-4000:])
    if err.strip():
        print("stderr:", err[-800:])
    print("exit", code)
    return code, out


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = c.open_sftp()
    sftp.put(str(ROOT / "scripts/backup.sh"), f"{REMOTE}/scripts/backup.sh")
    sftp.close()
    print("ok scripts/backup.sh")

    cron_line = (
        "30 2 * * * cd /opt/sanad && /bin/bash /opt/sanad/scripts/backup.sh "
        ">> /var/log/sanad/backup.log 2>&1"
    )
    install = r"""
set -e
chmod +x /opt/sanad/scripts/backup.sh
mkdir -p /var/log/sanad /opt/sanad/backups
tmp=$(mktemp)
crontab -l 2>/dev/null | grep -v 'scripts/backup.sh' > "$tmp" || true
echo '30 2 * * * cd /opt/sanad && /bin/bash /opt/sanad/scripts/backup.sh >> /var/log/sanad/backup.log 2>&1' >> "$tmp"
crontab "$tmp"
rm -f "$tmp"
echo '--- crontab ---'
crontab -l
echo '--- backup now ---'
cd /opt/sanad && /bin/bash /opt/sanad/scripts/backup.sh
echo '--- last backups ---'
ls -lh /opt/sanad/backups | tail -8
"""
    code, _ = run(c, install, timeout=180)
    c.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
