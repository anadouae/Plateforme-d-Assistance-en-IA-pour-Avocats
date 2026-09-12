#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/stt_quality.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/core/config.py",
    "backend/tests/test_dictation_pipeline.py",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    remote = f"{REMOTE}/{rel}"
    c.exec_command(f"mkdir -p {'/'.join(remote.split('/')[:-1])}")
    sftp.put(str(ROOT / rel), remote)
    print("ok", rel)
sftp.close()

cmd = (
    f"cd {REMOTE} && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "up -d --force-recreate backend 2>&1 && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 && "
    "sleep 8 && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python -m pytest tests/test_dictation_pipeline.py -q --tb=line 2>&1"
)
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace")[-2000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-600:])
c.close()
print("done")
