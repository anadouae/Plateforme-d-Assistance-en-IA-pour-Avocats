#!/usr/bin/env python3
"""Deploy security + LexHub branding pass."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/documents.py",
    "backend/app/api/auth.py",
    "backend/app/api/corpus.py",
    "backend/app/api/dictation.py",
    "backend/app/services/totp.py",
    "backend/app/services/extraction.py",
    "backend/app/services/language.py",
    "backend/app/services/local_llm.py",
    "backend/app/services/agent.py",
    "backend/app/services/document_pipeline.py",
    "backend/app/services/email.py",
    "docker-compose.lexhub.yml",
    "deploy/Caddyfile.lexhub",
    "frontend/public/manifest.json",
    "frontend/public/logo-lexhub-cube.png",
    "frontend/src/store/auth.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/components/brand/sanad-logo.tsx",
    "frontend/src/components/brand/sanad-page-loader.tsx",
    "frontend/src/components/brand/sanad-animated-logo.tsx",
    "frontend/src/components/brand/sanad-logo-animated.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/components/layout/app-shell.tsx",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/globals.css",
    "frontend/src/hooks/use-cabinet-realtime.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("MISSING", rel)
        continue
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
# Ensure ENCRYPTION_KEY present (do not invent a new one — keep existing from .env)
if [ -f .env.vps ] && ! grep -q '^ENCRYPTION_KEY=.\+' .env.vps; then
  echo 'WARNING: ENCRYPTION_KEY missing in .env.vps'
fi
grep -q '^LLM_OPENAI_STRICT=' .env.vps && sed -i 's/^LLM_OPENAI_STRICT=.*/LLM_OPENAI_STRICT=true/' .env.vps || echo 'LLM_OPENAI_STRICT=true' >> .env.vps
grep -q '^DICTATION_OPENAI_ONLY=' .env.vps && sed -i 's/^DICTATION_OPENAI_ONLY=.*/DICTATION_OPENAI_ONLY=true/' .env.vps || echo 'DICTATION_OPENAI_ONLY=true' >> .env.vps
grep -q '^WHISPER_ENABLED=' .env.vps && sed -i 's/^WHISPER_ENABLED=.*/WHISPER_ENABLED=false/' .env.vps || echo 'WHISPER_ENABLED=false' >> .env.vps
grep -q '^OPENAI_MODEL=' .env.vps && sed -i 's/^OPENAI_MODEL=.*/OPENAI_MODEL=gpt-4o/' .env.vps || echo 'OPENAI_MODEL=gpt-4o' >> .env.vps
cp deploy/Caddyfile.lexhub /etc/caddy/Caddyfile
systemctl reload caddy 2>&1 || systemctl restart caddy 2>&1 || true
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -30
sleep 5
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.core.config import settings; print(settings.OPENAI_MODEL, settings.LLM_OPENAI_STRICT, settings.DICTATION_OPENAI_ONLY, settings.WHISPER_ENABLED)"
curl -sI https://lexhub.space/ | head -8
curl -s -o /dev/null -w 'corpus_stats_http=%{http_code}\n' https://lexhub.space/api/corpus/stats
"""
_, o, e = c.exec_command(cmd, timeout=500)
print(o.read().decode(errors="replace")[-7000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-1500:])
c.close()
print("done")
