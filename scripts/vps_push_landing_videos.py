#!/usr/bin/env python3
"""Deploy landing video hero + popup visuals (compressed public/videos)."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/components/home/video-carousel.tsx",
    "frontend/src/components/billing/lex-product-modal.tsx",
    "frontend/src/styles/sanad-ui.css",
]

VIDEOS = [
    "frontend/public/videos/hero-lake.mp4",
    "frontend/public/videos/hero-ocean.mp4",
    "frontend/public/videos/hero-desk.mp4",
    "frontend/public/videos/popup-justice.mp4",
    "frontend/public/videos/popup-brand.mp4",
    "frontend/public/videos/popup-workspace.mp4",
]


def run(c, cmd, timeout=120):
    print(">>", cmd[:200], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    o.channel.settimeout(timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-3000:], flush=True)
    print("exit", code, flush=True)
    return code


print("connect…", flush=True)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60, auth_timeout=45)
print("connected", flush=True)

sftp = c.open_sftp()
for rel in FILES + VIDEOS:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel, flush=True)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 30)
    print(f"put {rel}…", flush=True)
    sftp.put(str(local), remote)
    print("ok", rel, f"{local.stat().st_size // 1024}KB", flush=True)
sftp.close()

# Soft prune cron (no --volumes)
PRUNE = (
    "#!/bin/bash\n"
    "docker builder prune -af --filter until=168h >/dev/null 2>&1 || true\n"
    "docker image prune -f >/dev/null 2>&1 || true\n"
)
sftp = c.open_sftp()
run(c, "mkdir -p /opt/sanad/scripts", 20)
with sftp.file("/opt/sanad/scripts/docker-soft-prune.sh", "w") as f:
    f.write(PRUNE)
sftp.close()
run(c, "chmod +x /opt/sanad/scripts/docker-soft-prune.sh", 20)
run(
    c,
    "crontab -l 2>/dev/null | grep -v docker-soft-prune > /tmp/cron.sanad || true; "
    "echo '15 4 * * 0 /opt/sanad/scripts/docker-soft-prune.sh >> /var/log/sanad-docker-prune.log 2>&1' >> /tmp/cron.sanad; "
    "crontab /tmp/cron.sanad; crontab -l | grep soft-prune",
    30,
)

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend",
    90,
)
time.sleep(8)
run(
    c,
    "curl -sS -o /dev/null -w 'home=%{http_code} lake=%{http_code}\\n' "
    "https://lexhub.space/ https://lexhub.space/videos/hero-lake.mp4",
    40,
)
c.close()
print("DONE", flush=True)
