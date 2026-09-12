#!/usr/bin/env python3
"""Force ChatGPT (OpenAI gpt-4o) for all text AI on LexHub VPS."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/core/config.py",
    "backend/app/services/free_llm_router.py",
    "backend/app/services/local_llm.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_clarify.py",
    "backend/app/services/plaidoirie_case_compose.py",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/services/cle_de_barre.py",
    "backend/app/services/ollama_summarize.py",
    "docker-compose.yml",
    "docker-compose.lexhub.yml",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
# Ensure env forces ChatGPT
if [ -f .env.vps ]; then
  grep -q '^OPENAI_MODEL=' .env.vps && sed -i 's/^OPENAI_MODEL=.*/OPENAI_MODEL=gpt-4o/' .env.vps || echo 'OPENAI_MODEL=gpt-4o' >> .env.vps
  grep -q '^LLM_FORCE_OPENAI=' .env.vps && sed -i 's/^LLM_FORCE_OPENAI=.*/LLM_FORCE_OPENAI=true/' .env.vps || echo 'LLM_FORCE_OPENAI=true' >> .env.vps
  grep -q '^LLM_USE_GROQ_FOR_CHAT=' .env.vps && sed -i 's/^LLM_USE_GROQ_FOR_CHAT=.*/LLM_USE_GROQ_FOR_CHAT=false/' .env.vps || echo 'LLM_USE_GROQ_FOR_CHAT=false' >> .env.vps
  grep -q '^LLM_USE_GROQ_FOR_WEB=' .env.vps && sed -i 's/^LLM_USE_GROQ_FOR_WEB=.*/LLM_USE_GROQ_FOR_WEB=false/' .env.vps || echo 'LLM_USE_GROQ_FOR_WEB=false' >> .env.vps
fi
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d backend celery-worker 2>&1 | tail -15
sleep 20
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
from app.services.free_llm_router import chat_free_tier
print('FORCE', settings.LLM_FORCE_OPENAI)
print('MODEL', settings.OPENAI_MODEL)
print('KEY', bool((settings.OPENAI_API_KEY or '').strip()))
# Simulate dictation preferred=mistral — must still hit openai when FORCE
text, prov = chat_free_tier(
    'Reponds uniquement: ALL_GPT_OK',
    'Test.',
    preferred='mistral',
    max_tokens=20,
    temperature=0,
    allow_ollama=False,
)
print('provider', prov)
print('reply', repr((text or '')[:60]))
assert 'openai' in (prov or ''), prov
assert text, 'empty'
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-900:])
c.close()
print("DONE")
