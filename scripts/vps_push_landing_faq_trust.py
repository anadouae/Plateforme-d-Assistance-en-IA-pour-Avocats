#!/usr/bin/env python3
"""Deploy landing FAQ / trust strip / pain / security page (inspiré LegalTech EU, contenu MA)."""
from pathlib import Path
import time
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "frontend/src/lib/landing-faq.ts",
    "frontend/src/components/home/landing-faq.tsx",
    "frontend/src/components/home/landing-compliance-strip.tsx",
    "frontend/src/components/home/landing-pain-section.tsx",
    "frontend/src/components/home/home-page-content.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/components/layout/public-footer.tsx",
]


def run(c, cmd, timeout=120):
    print(">>", cmd[:200], flush=True)
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = out + (("\n" + err) if err.strip() else "")
    if text.strip():
        print(text[-2500:], flush=True)
    print("exit", code, flush=True)
    return code


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=45, banner_timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel, flush=True)
        continue
    remote = f"{REMOTE}/{rel}"
    parent = str(Path(remote).parent).replace("\\", "/")
    run(c, f"mkdir -p {parent}", 20)
    sftp.put(str(local), remote)
    print("ok", rel, flush=True)
sftp.close()

run(
    c,
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"restart frontend 2>&1 | tail -20",
    120,
)
time.sleep(12)
run(c, "curl -sS -o /dev/null -w 'home=%{http_code} sec=%{http_code}\\n' https://lexhub.space/ https://lexhub.space/securite", 40)
c.close()
print("DONE", flush=True)
