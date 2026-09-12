#!/usr/bin/env python3
"""Audit VPS: all text AI must route to ChatGPT (OpenAI)."""
import paramiko

PASSWORD = "P@s$wiy.O0p"
cmd = r"""
cd /opt/sanad
echo '=== ENV ==='
grep -E '^(OPENAI_MODEL|OPENAI_API_KEY|LLM_FORCE_OPENAI|LLM_OPENAI_STRICT|LLM_USE_GROQ|LLM_PROVIDER)=' .env.vps 2>/dev/null | sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=***SET***/'
echo '=== COMPOSE LEXHUB ==='
grep -E 'LLM_FORCE_OPENAI|OPENAI_MODEL' docker-compose.lexhub.yml || true
echo '=== CONTAINER ENV ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv | grep -E '^(OPENAI_MODEL|LLM_FORCE_OPENAI|LLM_OPENAI_STRICT|LLM_USE_GROQ|LLM_PROVIDER|OPENAI_API_KEY)=' | sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=***SET***/'
echo '=== CODE FORCE ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend grep -n 'LLM_FORCE_OPENAI\|preferred = "openai"\|force_openai' app/core/config.py app/services/free_llm_router.py app/services/dictation.py app/services/plaidoirie_clarify.py app/services/cle_de_barre.py app/services/local_llm.py 2>/dev/null | head -40
echo '=== LIVE ROUTER TEST ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.config import settings
from app.services.free_llm_router import chat_free_tier, router_status

assert settings.LLM_FORCE_OPENAI is True, settings.LLM_FORCE_OPENAI
assert (settings.OPENAI_API_KEY or '').strip(), 'no openai key'
assert 'gpt-4o' in (settings.OPENAI_MODEL or ''), settings.OPENAI_MODEL

st = router_status().get('openai') or {}
print('openai_status', st)

# Even if caller asks mistral, FORCE must hit openai
for pref in ('mistral', 'groq', 'auto', 'openai'):
    text, prov = chat_free_tier(
        f'Reponds uniquement: OK_{pref.upper()}',
        'Une ligne.',
        preferred=pref,
        max_tokens=16,
        temperature=0,
        allow_ollama=False,
    )
    print(f'pref={pref} -> provider={prov} reply={(text or "")[:40]!r}')
    assert prov and 'openai' in prov, (pref, prov)
    assert text, (pref, text)

# local_llm path
from app.services.local_llm import _normalize_chat_provider, _call_chat_cloud
assert _normalize_chat_provider('mistral') == 'openai'
assert _normalize_chat_provider('auto') == 'openai'
raw = _call_chat_cloud('Reponds uniquement: LOCAL_OK', 'Test.')
print('local_llm', repr((raw or '')[:40]))
assert raw and 'LOCAL' in raw.upper()

# dictation helper default
import inspect
from app.services import dictation as d
sig = inspect.signature(d._llm)
assert sig.parameters['preferred'].default == 'openai', sig.parameters['preferred'].default

print('AUDIT_OK_ALL_CHATGPT')
PY
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR", err[-1200:])
c.close()
