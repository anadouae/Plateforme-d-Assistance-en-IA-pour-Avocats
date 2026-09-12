#!/usr/bin/env python3
"""Deploy STT mic + anti-hallucination fixes to lexhub.space."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "P@s$wiy.O0p")
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/core/config.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/stt_quality.py",
    "backend/app/services/dictation.py",
    "backend/app/services/audio_chunks.py",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]


def main() -> int:
    for rel in FILES:
        if not (ROOT / rel).exists():
            print("MISSING", rel, file=sys.stderr)
            return 1

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting {USER}@{HOST} …")
    c.connect(HOST, username=USER, password=PASSWORD, timeout=60, banner_timeout=120)
    sftp = c.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        remote = f"{REMOTE}/{rel}"
        # ensure remote dir
        parts = remote.rsplit("/", 1)[0]
        try:
            sftp.stat(parts)
        except OSError:
            c.exec_command(f"mkdir -p {parts}", timeout=30)
        sftp.put(str(local), remote)
        print("uploaded", rel)
    sftp.close()

    env_fix = (
        f"cd {REMOTE} && "
        f"touch .env.vps && "
        f"grep -q '^WHISPER_DENOISE=' .env.vps && "
        f"sed -i 's/^WHISPER_DENOISE=.*/WHISPER_DENOISE=false/' .env.vps || "
        f"echo 'WHISPER_DENOISE=false' >> .env.vps; "
        f"grep -q '^WHISPER_GAIN_DB=' .env.vps && "
        f"sed -i 's/^WHISPER_GAIN_DB=.*/WHISPER_GAIN_DB=6.0/' .env.vps || "
        f"echo 'WHISPER_GAIN_DB=6.0' >> .env.vps; "
        f"grep -E 'WHISPER_DENOISE|WHISPER_GAIN' .env.vps"
    )
    _, o, e = c.exec_command(env_fix, timeout=30)
    print("env:", o.read().decode(errors="replace").strip())
    err = e.read().decode(errors="replace").strip()
    if err:
        print("env_err:", err[-500:])

    restart = (
        f"cd {REMOTE} && "
        f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"--env-file .env.vps up -d --force-recreate backend celery-worker frontend 2>&1"
    )
    print("Restarting backend + celery + frontend …")
    _, o, e = c.exec_command(restart, timeout=300)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print(out[-3000:] if out else "(no stdout)")
    if err.strip():
        print(err[-1000:], file=sys.stderr)

    verify = (
        f"cd {REMOTE} && "
        f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps 2>&1; "
        f"echo '---'; "
        f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
        f"printenv WHISPER_DENOISE WHISPER_GAIN_DB DICTATION_LOCAL_ONLY 2>&1; "
        f"echo '---'; "
        f"curl -sf -o /dev/null -w '%{{http_code}}\\n' https://lexhub.space/ || echo fail_web; "
        f"curl -sf -o /dev/null -w '%{{http_code}}\\n' http://127.0.0.1:8001/health/live || echo fail_api"
    )
    _, o, e = c.exec_command(verify, timeout=90)
    print(o.read().decode(errors="replace")[-2500:])
    err = e.read().decode(errors="replace").strip()
    if err:
        print(err[-800:], file=sys.stderr)
    c.close()
    print("DEPLOY DONE → https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
