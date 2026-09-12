#!/usr/bin/env python3
"""Copy RESEND/SMTP email settings from /opt/sanad/.env into .env.vps and recreate backend."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)

cmd = r"""
set -e
cd /opt/sanad
python3 - <<'PY'
from pathlib import Path

KEYS = [
    "RESEND_API_KEY",
    "EMAIL_FROM",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM",
    "SMTP_TLS",
]

def parse(path: Path) -> dict[str, str]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out

src = parse(Path(".env"))
dst_path = Path(".env.vps")
dst = parse(dst_path)
changed = []
for k in KEYS:
    if k in src and src[k] and dst.get(k) != src[k]:
        dst[k] = src[k]
        changed.append(k)

# Prefer Resend if key present; keep SMTP as fallback
lines = dst_path.read_text(encoding="utf-8", errors="replace").splitlines()
kept = []
seen = set()
for line in lines:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        kept.append(line)
        continue
    k = s.split("=", 1)[0].strip()
    if k in KEYS:
        kept.append(f"{k}={dst[k]}")
        seen.add(k)
    else:
        kept.append(line)
for k in KEYS:
    if k in dst and k not in seen:
        kept.append(f"{k}={dst[k]}")

dst_path.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")
print("updated_keys", ",".join(changed) if changed else "(none — already synced)")
print("RESEND_set", bool(dst.get("RESEND_API_KEY")))
print("SMTP_HOST", dst.get("SMTP_HOST", ""))
print("EMAIL_FROM", dst.get("EMAIL_FROM") or dst.get("SMTP_FROM", ""))
PY

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --force-recreate backend celery-worker 2>&1 | tail -15
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps exec -T backend python - <<'PY'
from app.services.email import email_configured
from app.core.config import settings
print("email_configured", email_configured())
print("RESEND_set", bool((settings.RESEND_API_KEY or "").strip()))
print("SMTP_HOST", repr(settings.SMTP_HOST))
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print(err)
c.close()
