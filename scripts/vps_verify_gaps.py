#!/usr/bin/env python3
"""Verify remaining gaps on VPS + local vs intended LexHub hardening."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"

checks_local = []

# Local file checks
def has(path, needle):
    p = ROOT / path
    if not p.exists():
        return False, f"MISSING FILE {path}"
    t = p.read_text(encoding="utf-8", errors="replace")
    return (needle in t), path

items = [
    ("backend/app/core/config.py", "LLM_OPENAI_STRICT: bool = True"),
    ("backend/app/core/config.py", "DICTATION_OPENAI_ONLY: bool = True"),
    ("backend/app/core/config.py", "WHISPER_ENABLED: bool = False"),
    ("backend/app/api/corpus.py", "Depends(get_current_user)"),
    ("backend/app/api/documents.py", "require_not_assistant"),
    ("backend/app/api/auth.py", "ADMIN_WEBVOICE"),
    ("backend/app/services/totp.py", 'issuer: str = "LexHub"'),
    ("backend/app/services/extraction.py", "zip-bomb"),
    ("frontend/public/manifest.json", '"name": "LexHub"'),
    ("frontend/public/logo-lexhub-cube.png", ""),  # exists
    ("frontend/src/store/auth.ts", "lexhub_token"),
    ("frontend/src/lib/api.ts", "lexhub_token"),
    ("frontend/src/components/brand/sanad-logo.tsx", "logo-lexhub-cube"),
    ("deploy/Caddyfile.lexhub", "max-age=31536000, immutable"),
    ("docker-compose.lexhub.yml", "LLM_OPENAI_STRICT: \"true\""),
    ("docker-compose.lexhub.yml", "ENCRYPTION_KEY: ${ENCRYPTION_KEY}"),
]

print("=== LOCAL ===")
for path, needle in items:
    p = ROOT / path
    if not p.exists():
        print("FAIL missing", path)
        continue
    if not needle:
        print("OK exists", path)
        continue
    t = p.read_text(encoding="utf-8", errors="replace") if p.suffix != ".png" else ""
    if p.suffix == ".png" or needle in t:
        print("OK", path, "→", needle[:40])
    else:
        print("FAIL", path, "missing", needle[:60])

# Remaining Sanad product strings (not CSS)
print("\n=== SANAD leftovers (sample) ===")
import re
for glob in [
    "frontend/public/manifest.json",
    "backend/app/services/language.py",
    "backend/app/services/local_llm.py",
    "backend/app/services/agent.py",
    "backend/app/services/totp.py",
]:
    p = ROOT / glob
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    hits = len(re.findall(r"\bSanad\b", t))
    print(f"{glob}: Sanad={hits}")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
cmd = r"""
cd /opt/sanad
echo '=== PROD CONFIG ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
keys = [
 'OPENAI_MODEL','LLM_FORCE_OPENAI','LLM_OPENAI_STRICT','LLM_USE_FREE_ROUTER',
 'DICTATION_OPENAI_ONLY','DICTATION_STT_PREFER_GROQ','WHISPER_ENABLED',
 'DICTATION_POLISH_USE_LLM','OPENAI_API_KEY'
]
for k in keys:
    v = getattr(settings, k, None)
    if k.endswith('KEY') and v:
        v = (str(v)[:8] + '…') if v else ''
    print(f'{k}={v}')
PY
echo '=== HTTP ==='
curl -sI https://lexhub.space/ | grep -iE 'HTTP/|cache-control|strict-transport|x-frame|x-content|permissions'
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
curl -s -o /dev/null -w 'corpus=%{http_code}\n' https://lexhub.space/api/corpus/stats
curl -s -o /dev/null -w 'manifest=%{http_code}\n' https://lexhub.space/manifest.json
curl -s https://lexhub.space/manifest.json | head -c 200; echo
curl -s -o /dev/null -w 'logo_lexhub=%{http_code}\n' https://lexhub.space/logo-lexhub-cube.png
echo '=== MFA / delete code on VPS ==='
grep -n 'ADMIN_WEBVOICE\|_require_not_assistant\|_zip-bomb\|LexHub' backend/app/api/auth.py backend/app/api/documents.py backend/app/services/extraction.py backend/app/services/totp.py 2>/dev/null | head -30
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-2000:])
c.close()
