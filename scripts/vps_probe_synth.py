#!/usr/bin/env python3
import paramiko
PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
cmd = r"""
cd /opt/sanad
echo '=== recent synth / LLM errors ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --tail 200 2>&1 | grep -iE 'synth|mistral|groq|llm|timeout|error|0566cb46' | tail -40
echo '=== quick synth probe ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.core.database import SessionLocal
from app.models import Document
from app.services.agent import generate_synthesis
db=SessionLocal()
doc=db.query(Document).filter(Document.id=='0566cb46-cb05-4b8f-b0ce-9b06300d07a0').first()
text=(doc.extracted_text or '')[:8000]
print('chars_used', len(text))
try:
    data=generate_synthesis(doc.original_name, text, language='ar')
    s=(data.get('summary') or '')[:200]
    print('summary_len', len(data.get('summary') or ''))
    print('summary_head', s.replace('\n',' | '))
    print('attention', data.get('attention_points'))
except Exception as e:
    print('FAIL', type(e).__name__, e)
db.close()
PY
"""
_,o,e=c.exec_command(cmd, timeout=180)
print(o.read().decode(errors='replace'))
print(e.read().decode(errors='replace')[-1500:])
c.close()
