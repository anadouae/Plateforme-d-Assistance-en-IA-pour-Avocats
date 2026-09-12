#!/usr/bin/env python3
"""Push: qualité AR (Groq first) + aperçu Chrome qui ne tue plus la dictée."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/whisper_stt.py",
    "backend/app/core/config.py",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = f"""
cd {REMOTE}
# Prefer large model for Arabic quality
grep -q '^GROQ_WHISPER_MODEL=' .env 2>/dev/null \\
  && sed -i 's/^GROQ_WHISPER_MODEL=.*/GROQ_WHISPER_MODEL=whisper-large-v3/' .env \\
  || echo 'GROQ_WHISPER_MODEL=whisper-large-v3' >> .env
grep -q '^DICTATION_LOCAL_ONLY=' .env 2>/dev/null \\
  && sed -i 's/^DICTATION_LOCAL_ONLY=.*/DICTATION_LOCAL_ONLY=false/' .env \\
  || echo 'DICTATION_LOCAL_ONLY=false' >> .env
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1
sleep 5
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend \\
  printenv DICTATION_LOCAL_ONLY GROQ_WHISPER_MODEL WHISPER_MODEL 2>&1 | head -20
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace")[-3000:])
print(e.read().decode(errors="replace")[-500:])
c.close()
print("done")
