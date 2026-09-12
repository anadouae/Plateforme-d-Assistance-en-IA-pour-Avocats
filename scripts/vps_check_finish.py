#!/usr/bin/env python3
"""Check VPS env readiness (no secrets printed)."""
import paramiko
import re

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=30)

_, out, err = c.exec_command("cat /opt/sanad/.env")
raw = out.read().decode(errors="replace")
keys = {}
for line in raw.splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, _, v = line.partition("=")
        keys[k.strip()] = v.strip()

def mask(k):
    v = keys.get(k, "")
    if not v:
        return "(missing)"
    if "SECRET" in k or "PASSWORD" in k or "ENCRYPTION" in k:
        return f"set(len={len(v)})"
    if "KEY" in k and k.startswith("TURNSTILE"):
        return v[:12] + "..."
    return v

for k in [
    "ENVIRONMENT",
    "SECRET_KEY",
    "ENCRYPTION_KEY",
    "TURNSTILE_SITE_KEY",
    "TURNSTILE_SECRET_KEY",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_FROM",
    "SMTP_TLS",
    "SEED_DEMO_DATA",
]:
    print(f"{k}={mask(k)}")

sk = keys.get("SECRET_KEY", "")
print(f"SECRET_KEY_ok={len(sk) >= 32 and 'change' not in sk.lower() and 'dev-secret' not in sk.lower()}")
print(f"TURNSTILE_ok={'TURNSTILE_SITE_KEY' in keys and 'TURNSTILE_SECRET_KEY' in keys and not keys.get('TURNSTILE_SITE_KEY','').startswith('1x000')}")
print(f"SMTP_configured={bool(keys.get('SMTP_HOST') and keys.get('SMTP_HOST') not in ('mailhog','localhost'))}")

_, o2, _ = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps --format '{{.Name}} {{.Status}}' 2>&1 | head -15"
)
print("--- containers ---")
print(o2.read().decode(errors="replace"))
c.close()
