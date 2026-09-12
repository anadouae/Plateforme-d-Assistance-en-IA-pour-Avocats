#!/usr/bin/env python3
"""Deploy Phase 2 dictation pipeline + run tests on VPS."""
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/audio_chunks.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/core/config.py",
    "backend/app/api/dictation.py",
    "backend/tests/test_dictation_pipeline.py",
    "frontend/src/lib/api.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "docs/PIPELINE_DICTEE_AR.md",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    remote_dir = "/".join(remote.split("/")[:-1])
    c.exec_command(f"mkdir -p {remote_dir}")
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = (
    f"cd {REMOTE} && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "up -d --force-recreate backend 2>&1 && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "restart frontend 2>&1 && "
    "sleep 8 && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "exec -T backend python -m pytest tests/test_dictation_pipeline.py -q --tb=line 2>&1"
)
_, o, e = c.exec_command(cmd, timeout=240)
out = o.read().decode(errors="replace")
err = e.read().decode(errors="replace")
print(out[-2500:])
if err.strip():
    print("stderr:", err[-1000:])
c.close()
print("done")
