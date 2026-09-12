#!/usr/bin/env python3
"""Finish remaining gaps: rate limits, branding, favicon, deploy FE+BE."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/api/settings.py",
    "backend/app/api/documents.py",
    "backend/app/api/auth.py",
    "backend/app/api/corpus.py",
    "backend/app/services/language.py",
    "backend/app/services/hibp.py",
    "backend/app/services/free_llm_router.py",
    "backend/app/services/extraction.py",
    "deploy/Caddyfile.lexhub",
    "frontend/next.config.mjs",
    "frontend/public/manifest.json",
    "frontend/public/logo-lexhub-cube.png",
    "frontend/src/components/brand/sanad-logo.tsx",
    "frontend/src/components/brand/sanad-page-loader.tsx",
    "frontend/src/components/brand/sanad-animated-logo.tsx",
    "frontend/src/components/brand/sanad-logo-animated.tsx",
    "frontend/src/components/auth/sanad-turnstile.tsx",
    "frontend/src/components/onboarding/sanad-onboarding.tsx",
    "frontend/src/components/auth/auth-product-demo.tsx",
    "frontend/src/components/auth/unified-auth.tsx",
    "frontend/src/components/auth/auth-layout.tsx",
    "frontend/src/components/auth/auth-hero-side.tsx",
    "frontend/src/components/layout/public-navbar.tsx",
    "frontend/src/components/layout/public-footer.tsx",
    "frontend/src/components/layout/legal-page-layout.tsx",
    "frontend/src/app/checkout/page.tsx",
    "frontend/src/app/about/page.tsx",
    "frontend/src/app/forgot-password/page.tsx",
    "frontend/src/app/fonctionnalites/page.tsx",
    "frontend/src/hooks/use-speech-input.ts",
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
set -e
cd /opt/sanad
# Keep OpenAI-only flags
for kv in 'LLM_OPENAI_STRICT=true' 'LLM_USE_FREE_ROUTER=false' 'DICTATION_OPENAI_ONLY=true' 'WHISPER_ENABLED=false' 'OPENAI_MODEL=gpt-4o' 'DICTATION_POLISH_USE_LLM=true'; do
  key="${kv%%=*}"; val="${kv#*=}"
  if grep -q "^${key}=" .env.vps 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" .env.vps
  else
    echo "${key}=${val}" >> .env.vps
  fi
done
cp deploy/Caddyfile.lexhub /etc/caddy/Caddyfile
systemctl reload caddy 2>&1 || systemctl restart caddy 2>&1 || true
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -40
sleep 8
echo '--- config ---'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.core.config import settings; print('model', settings.OPENAI_MODEL); print('strict', settings.LLM_OPENAI_STRICT); print('dict_oa', settings.DICTATION_OPENAI_ONLY); print('whisper', settings.WHISPER_ENABLED)"
echo '--- smoke ---'
curl -sI https://lexhub.space/ | head -12
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
curl -s -o /dev/null -w 'favicon=%{http_code}\n' https://lexhub.space/favicon.ico
curl -s -o /dev/null -w 'logo=%{http_code}\n' https://lexhub.space/logo-lexhub-cube.png
curl -s -o /dev/null -w 'manifest=%{http_code}\n' https://lexhub.space/manifest.json
curl -s https://lexhub.space/manifest.json | head -c 200; echo
curl -s -o /dev/null -w 'corpus=%{http_code}\n' https://lexhub.space/api/corpus/stats
curl -sI https://lexhub.space/sanad-landing-v3.html | head -8
grep -n 'export_pdf\|export_docx\|cabinet_logo' /opt/sanad/backend/app/api/plaidoirie_templates.py /opt/sanad/backend/app/api/settings.py | head -20
grep -n 'require_not_assistant' /opt/sanad/backend/app/api/documents.py | head -10
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace")[-9000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-2000:])
c.close()
print("done")
