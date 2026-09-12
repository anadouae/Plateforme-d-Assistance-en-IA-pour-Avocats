#!/usr/bin/env python3
"""Deploy expert-hardening fixes to lexhub VPS."""
from __future__ import annotations

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
    "backend/app/main.py",
    "backend/app/api/auth.py",
    "backend/app/api/settings.py",
    "backend/app/services/email.py",
    "backend/app/api/team.py",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/components/layout/public-footer.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/auth/auth-layout.tsx",
    "frontend/src/components/auth/sanad-turnstile.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/template-picker.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/components/onboarding/sanad-onboarding.tsx",
    "frontend/src/hooks/use-onboarding.ts",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/lib/onboarding-steps.ts",
    "frontend/src/app/agenda/page.tsx",
    "frontend/src/app/settings/page.tsx",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/app/mentions-legales/page.tsx",
    "frontend/src/app/confidentialite/page.tsx",
    "frontend/src/app/securite/page.tsx",
    "frontend/src/app/admin/page.tsx",
    "frontend/Dockerfile.prod",
]


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str]:
    _, out, err = client.exec_command(cmd, timeout=timeout)
    code = out.channel.recv_exit_status()
    text = out.read().decode(errors="replace") + err.read().decode(errors="replace")
    return code, text


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=40)

    sftp = client.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            print("SKIP missing", rel)
            continue
        remote = f"{REMOTE}/{rel}"
        run(client, f"mkdir -p $(dirname {remote!r})" if "'" not in remote else f"mkdir -p \"$(dirname \"{remote}\")\"")
        # brackets in path: use quoted mkdir
        parent = str(Path(remote).parent).replace("\\", "/")
        run(client, f'mkdir -p "{parent}"')
        sftp.put(str(local), remote)
        print("uploaded", rel)
    sftp.close()

    print("recreate backend...")
    code, text = run(
        client,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1",
        timeout=180,
    )
    print(text[-1500:])
    if code != 0:
        print("backend recreate failed", code)
        return 1

    print("build+recreate frontend (prod Dockerfile) — may take several minutes...")
    code, text = run(
        client,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml build frontend 2>&1",
        timeout=900,
    )
    print(text[-2500:])
    if code != 0:
        print("PROD BUILD FAILED — falling back to in-container next build+start with volume")
        # Fallback compose snippet via sed is messy; run alternate command on existing Dockerfile
        fallback = f"""cd {REMOTE} && cat > /tmp/lexhub-frontend-fallback.yml <<'EOF'
services:
  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: https://lexhub.space
      NODE_OPTIONS: --max-old-space-size=1536
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: ["sh", "-c", "npm run build && npx next start -H 0.0.0.0 -p 3000"]
    restart: unless-stopped
EOF
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml -f /tmp/lexhub-frontend-fallback.yml up -d --force-recreate --build frontend 2>&1
"""
        code2, text2 = run(client, fallback, timeout=900)
        print(text2[-2500:])
        if code2 != 0:
            return 1
    else:
        code, text = run(
            client,
            f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate frontend 2>&1",
            timeout=180,
        )
        print(text[-1500:])
        if code != 0:
            return 1

    time.sleep(12)
    _, env = run(
        client,
        "docker exec sanad-backend-1 printenv ENVIRONMENT SMTP_HOST 2>/dev/null; "
        "docker ps --filter name=sanad-frontend --format '{{.Status}} {{.Image}}'; "
        "docker exec sanad-frontend-1 sh -c 'ps aux | head -5' 2>/dev/null || true",
    )
    print(env)
    client.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        raise SystemExit(1)
