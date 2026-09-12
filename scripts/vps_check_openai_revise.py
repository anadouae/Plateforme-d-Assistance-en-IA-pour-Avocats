#!/usr/bin/env python3
"""Check OpenAI (ChatGPT API) on VPS for revise path."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
from app.services.free_llm_router import chat_free_tier, router_status

print('OPENAI_MODEL', settings.OPENAI_MODEL)
print('OPENAI_KEY', 'yes' if (settings.OPENAI_API_KEY or '').strip() else 'NO')
st = router_status()
print('openai_status', st.get('openai'))
text, prov = chat_free_tier(
    'Reponds uniquement le mot: OK_GPT',
    'Tu es un test. Une seule ligne.',
    preferred='openai',
    max_tokens=16,
    temperature=0,
    allow_ollama=False,
)
print('provider', prov)
print('reply', repr((text or '')[:100]))
PY
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-500:])
c.close()
