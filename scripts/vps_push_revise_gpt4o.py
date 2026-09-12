#!/usr/bin/env python3
"""Deploy revise = ChatGPT gpt-4o only (no weak fallback)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/free_llm_router.py",
    "backend/app/services/plaidoirie_revise.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -8
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.free_llm_router import chat_free_tier
text, prov = chat_free_tier(
    'Reponds uniquement: GPT4O_OK',
    'Test court.',
    preferred='openai',
    strict_preferred=True,
    allow_ollama=False,
    model_override='gpt-4o',
    max_tokens=20,
    temperature=0,
)
print('provider', prov)
print('reply', repr((text or '')[:80]))
assert prov.startswith('openai'), prov
assert text and 'GPT4O' in text.upper().replace('-','').replace('_',''), text
# also accept OK style
print('SMOKE_OK')
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
