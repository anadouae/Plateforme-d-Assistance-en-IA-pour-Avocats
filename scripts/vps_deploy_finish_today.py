#!/usr/bin/env python3
"""Deploy finish-today files + harden VPS secrets for production."""
from __future__ import annotations

import secrets
import sys
import time
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "docker-compose.lexhub.yml",
    "backend/app/services/email.py",
    "backend/app/api/team.py",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/components/redaction/template-picker.tsx",
]


def ssh_run(client: paramiko.SSHClient, cmd: str) -> str:
    _, out, err = client.exec_command(cmd, timeout=180)
    code = out.channel.recv_exit_status()
    text = out.read().decode(errors="replace") + err.read().decode(errors="replace")
    if code != 0:
        raise RuntimeError(f"cmd failed ({code}): {cmd}\n{text}")
    return text


def ensure_env_secrets(client: paramiko.SSHClient) -> None:
    raw = ssh_run(client, f"cat {REMOTE}/.env")
    keys = {}
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        keys[k.strip()] = v.strip()

    # Prefer values already running in the container (avoid rotating ENCRYPTION_KEY)
    try:
        running = ssh_run(
            client,
            "docker exec sanad-backend-1 sh -c "
            "'printf \"SECRET_KEY=%s\\nENCRYPTION_KEY=%s\\nENVIRONMENT=%s\\n\" "
            "\"$SECRET_KEY\" \"$ENCRYPTION_KEY\" \"$ENVIRONMENT\"'",
        )
        run_map = {}
        for line in running.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                run_map[k.strip()] = v.strip()
    except Exception:
        run_map = {}

    updates = []

    sk = keys.get("SECRET_KEY") or run_map.get("SECRET_KEY", "")
    weak = (
        not sk
        or len(sk) < 32
        or "change" in sk.lower()
        or "dev-secret" in sk.lower()
    )
    if weak:
        updates.append(f"SECRET_KEY={secrets.token_urlsafe(48)}")
    elif "SECRET_KEY" not in keys and sk:
        updates.append(f"SECRET_KEY={sk}")

    ek = keys.get("ENCRYPTION_KEY") or run_map.get("ENCRYPTION_KEY", "")
    if ek and "ENCRYPTION_KEY" not in keys:
        # Persist current key — do NOT rotate
        updates.append(f"ENCRYPTION_KEY={ek}")
    elif not ek:
        import base64

        updates.append(
            "ENCRYPTION_KEY="
            + base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        )

    if "ENVIRONMENT" not in keys:
        updates.append("ENVIRONMENT=production")
    if "SEED_DEMO_DATA" not in keys:
        updates.append("SEED_DEMO_DATA=false")

    # Keep MailHog until Brevo credentials are provided
    if not keys.get("SMTP_HOST"):
        updates.append("SMTP_HOST=mailhog")
        updates.append("SMTP_PORT=1025")
        updates.append("SMTP_TLS=false")
        updates.append("SMTP_FROM=Sanad <noreply@lexhub.space>")
    elif "SMTP_FROM" not in keys:
        updates.append("SMTP_FROM=Sanad <noreply@lexhub.space>")

    if not updates:
        print("env: secrets already OK")
        return

    for line in updates:
        key = line.split("=", 1)[0]
        ssh_run(client, f"sed -i '/^{key}=/d' {REMOTE}/.env")
    blob = "\n".join(updates) + "\n"
    sftp = client.open_sftp()
    with sftp.file(f"{REMOTE}/.env.append.tmp", "w") as f:
        f.write(blob)
    sftp.close()
    ssh_run(
        client,
        f"cat {REMOTE}/.env.append.tmp >> {REMOTE}/.env && rm {REMOTE}/.env.append.tmp",
    )
    print("env: updated", [u.split("=", 1)[0] for u in updates])


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=40)

    ensure_env_secrets(client)

    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"{REMOTE}/{rel}"
        ssh_run(client, f"mkdir -p $(dirname {remote})")
        sftp.put(str(local), remote)
        print("uploaded", rel)
    sftp.close()

    print("recreating backend+frontend...")
    out = ssh_run(
        client,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1",
    )
    print(out[-2000:])

    time.sleep(8)
    out = ssh_run(
        client,
        "docker exec sanad-backend-1 printenv | grep -E '^(ENVIRONMENT|SMTP_HOST|SEED_DEMO|TURNSTILE_SITE)=' ",
    )
    print("backend env:", out)
    out = ssh_run(client, "docker ps --filter name=sanad-backend --format '{{.Status}}'")
    print("backend status:", out)
    client.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        raise SystemExit(1)
