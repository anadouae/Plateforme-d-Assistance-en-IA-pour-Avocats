#!/usr/bin/env python3
"""Fix: download Arabic filenames, 80-char brief, preview Word, Corriger LLM, pièces failed."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/dictation.py",
    "backend/app/api/documents.py",
    "backend/app/core/config.py",
    "backend/app/services/dictation.py",
    "docker-compose.lexhub.yml",
    "frontend/src/components/documents/document-preview-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/lib/api.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

# Force polish LLM on VPS env + recreate
cmd = f"""
cd {REMOTE} && \
for f in .env .env.vps; do
  [ -f "$f" ] || continue
  grep -q '^DICTATION_POLISH_USE_LLM=' "$f" \\
    && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' "$f" \\
    || echo 'DICTATION_POLISH_USE_LLM=true' >> "$f"
done && \
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -40
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace")[-5000:])
err = e.read().decode(errors="replace")
if err:
    print("stderr:", err[-2000:])
c.close()
print("done")
