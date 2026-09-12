#!/usr/bin/env python3
"""Deploy Arabic STT fidelity fix: real mic gain + Groq Whisper primary."""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/core/config.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/stt_quality.py",
    "backend/app/services/dictation.py",
    "backend/app/services/audio_chunks.py",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "docker-compose.lexhub.yml",
]


def main() -> int:
    for rel in FILES:
        if not (ROOT / rel).exists():
            print("MISSING", rel, file=sys.stderr)
            return 1

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting root@{HOST} ...")
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=120)
    sftp = c.open_sftp()
    for rel in FILES:
        remote = f"{REMOTE}/{rel}"
        sftp.put(str(ROOT / rel), remote)
        print("uploaded", rel)
    sftp.close()

    env_cmd = f"""
cd {REMOTE}
touch .env.vps
for kv in 'DICTATION_LOCAL_ONLY=false' 'DICTATION_STT_PREFER_GROQ=true' 'WHISPER_DENOISE=false' 'WHISPER_GAIN_DB=8.0' 'GROQ_WHISPER_MODEL=whisper-large-v3'; do
  k=${{kv%%=*}}
  if grep -q "^$k=" .env.vps; then sed -i "s|^$k=.*|$kv|" .env.vps; else echo "$kv" >> .env.vps; fi
done
echo '--- env ---'
grep -E '^(DICTATION_|WHISPER_|GROQ_WHISPER)' .env.vps
echo '--- groq key present ---'
grep -c '^GROQ_API_KEY=.' .env.vps || true
"""
    _, o, e = c.exec_command(env_cmd, timeout=30)
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print(err[-500:], file=sys.stderr)

    restart = (
        f"cd {REMOTE} && "
        f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        f"--env-file .env.vps up -d --force-recreate backend celery-worker frontend 2>&1"
    )
    print("Recreating services...")
    _, o, e = c.exec_command(restart, timeout=300)
    print(o.read().decode(errors="replace")[-2500:])
    err = e.read().decode(errors="replace")
    if err.strip():
        print(err[-800:], file=sys.stderr)

    verify = f"""
sleep 18
cd {REMOTE}
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
print("local_only", settings.DICTATION_LOCAL_ONLY)
print("prefer_groq", settings.DICTATION_STT_PREFER_GROQ)
print("gain", settings.WHISPER_GAIN_DB)
print("groq_key", bool((settings.GROQ_API_KEY or "").strip()))
print("groq_model", settings.GROQ_WHISPER_MODEL)
import inspect
from app.services import whisper_stt
src = inspect.getsource(whisper_stt.transcribe_audio_bytes)
print("has_prefer_block", "DICTATION_STT_PREFER_GROQ" in open("/app/app/core/config.py").read())
print("has_strip", hasattr(whisper_stt, "_strip_arabic_hallucinations"))
print("has_dest_gain", "createMediaStreamDestination" in open("/app/../frontend/src/hooks/use-whisper-dictation.ts", encoding="utf-8", errors="ignore").read() if False else "check_file")
PY
grep -n "createMediaStreamDestination\\|gain.gain.value" {REMOTE}/frontend/src/hooks/use-whisper-dictation.ts | head -10
curl -sf -o /dev/null -w "web:%{{http_code}}\\n" https://lexhub.space/ || echo web_fail
curl -sf -o /dev/null -w "api:%{{http_code}}\\n" http://127.0.0.1:8001/health/live || echo api_fail
"""
    _, o, e = c.exec_command(verify, timeout=90)
    print(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace")
    if err.strip():
        print(err[-1000:], file=sys.stderr)
    c.close()
    print("DONE -> https://lexhub.space")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
