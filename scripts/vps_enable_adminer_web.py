#!/usr/bin/env python3
"""Expose Adminer on https://lexhub.space/_ops/db/ with HTTP basic auth (no tunnel)."""
from pathlib import Path
import secrets
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
SSH_PASSWORD = "P@s$wiy.O0p"
BASIC_USER = "douae"
BASIC_PASS = "LhDb-" + secrets.token_urlsafe(10)

CADDY = '''lexhub.space, www.lexhub.space {
	encode gzip zstd

	header {
		Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
		X-Content-Type-Options "nosniff"
		X-Frame-Options "DENY"
		Referrer-Policy "strict-origin-when-cross-origin"
		Permissions-Policy "camera=(), microphone=(self), geolocation=(), payment=()"
		-Server
		-X-Powered-By
	}

	handle /api/* {
		reverse_proxy 127.0.0.1:8001
	}

	handle /health* {
		reverse_proxy 127.0.0.1:8001
	}

	# Adminer (Postgres UI) — protégé par mot de passe navigateur
	handle /_ops/db {
		redir * /_ops/db/ permanent
	}
	handle_path /_ops/db/* {
		basic_auth {
			__BASIC_USER__ __BASIC_HASH__
		}
		reverse_proxy 127.0.0.1:8088
	}

	@nextstatic path /_next/static/*
	header @nextstatic Cache-Control "public, max-age=31536000, immutable"

	@staticassets {
		path /videos/* /fonts/* *.mp4 *.png *.jpg *.jpeg *.webp *.ico *.svg *.woff2
	}
	header @staticassets Cache-Control "public, max-age=604800, stale-while-revalidate=86400"

	@html {
		not path /_next/* /videos/* /fonts/* *.mp4 *.png *.jpg *.jpeg *.webp *.ico *.svg *.woff2 /_ops/*
	}
	header @html Cache-Control "no-store, must-revalidate"

	handle {
		reverse_proxy 127.0.0.1:3000
	}
}
'''

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=SSH_PASSWORD, timeout=60, banner_timeout=120)

# Generate Caddy bcrypt hash on the server
_, o, e = c.exec_command(
    f"docker run --rm caddy:2-alpine caddy hash-password --plaintext {BASIC_PASS!r}",
    timeout=120,
)
# shell quoting - better write password to stdin
# redo properly:
sftp = c.open_sftp()
# Write a tiny helper
helper = f"#!/bin/sh\nprintf '%s' '{BASIC_PASS}' | caddy hash-password\n"
# Use docker with env
cmd_hash = (
    "docker run --rm caddy:2-alpine "
    f"caddy hash-password --plaintext '{BASIC_PASS}'"
)
_, o, e = c.exec_command(cmd_hash, timeout=180)
h = o.read().decode(errors="replace").strip()
err = e.read().decode(errors="replace")
if not h.startswith("$"):
    print("hash failed", h, err)
    c.close()
    raise SystemExit(1)
print("hash_ok")

body = CADDY.replace("__BASIC_USER__", BASIC_USER).replace("__BASIC_HASH__", h)
local_caddy = ROOT / "deploy" / "Caddyfile.lexhub"
local_caddy.write_text(body, encoding="utf-8")

# Ensure adminer up + install caddyfile
sftp.put(str(local_caddy), "/opt/sanad/deploy/Caddyfile.lexhub")
# Also common path used by Caddy on host
for remote in ("/etc/caddy/Caddyfile", "/opt/sanad/Caddyfile", "/opt/sanad/deploy/Caddyfile.lexhub"):
    try:
        sftp.stat(remote if remote != "/opt/sanad/deploy/Caddyfile.lexhub" else remote)
        print("exists", remote)
    except OSError:
        print("missing", remote)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d adminer 2>&1 | tail -8
# Locate active Caddyfile
ls -la /etc/caddy/Caddyfile /opt/sanad/deploy/Caddyfile.lexhub 2>/dev/null || true
# If systemd caddy uses /etc/caddy/Caddyfile, sync it
if [ -f /etc/caddy/Caddyfile ]; then
  cp /opt/sanad/deploy/Caddyfile.lexhub /etc/caddy/Caddyfile
  caddy validate --config /etc/caddy/Caddyfile 2>&1 | tail -5
  systemctl reload caddy 2>&1 | tail -5 || caddy reload --config /etc/caddy/Caddyfile 2>&1 | tail -5
else
  echo NO_SYSTEM_CADDYFILE
  # maybe caddy in docker
  docker ps --format '{{.Names}}' | grep -i caddy || true
fi
sleep 2
curl -s -o /dev/null -w 'local_adminer:%{http_code}\n' http://127.0.0.1:8088/
curl -s -o /dev/null -w 'public_unauth:%{http_code}\n' https://lexhub.space/_ops/db/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-800:])
c.close()

cred_path = Path.home() / "Desktop" / "LexHub_Adminer_acces.txt"
cred_path.write_text(
    f"""Adminer LexHub (sans tunnel / sans pgAdmin)

URL: https://lexhub.space/_ops/db/

1) Mot de passe navigateur (popup Chrome):
   utilisateur: {BASIC_USER}
   mot de passe: {BASIC_PASS}

2) Ensuite écran Adminer:
   Système: PostgreSQL
   Serveur: postgres
   Utilisateur: sanad
   Mot de passe: sanad_secret
   Base: sanad

Ne partagez pas ce fichier.
""",
    encoding="utf-8",
)
print("CREDENTIALS saved to", cred_path)
print("URL https://lexhub.space/_ops/db/")
print("basic_user", BASIC_USER)
print("basic_pass", BASIC_PASS)
print("DONE")
