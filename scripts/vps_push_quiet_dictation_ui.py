#!/usr/bin/env python3
"""Push: hide STT tech messages; smarter polish LLM; rebuild FE+BE."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "backend/app/services/dictation.py",
    "docker-compose.lexhub.yml",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
# Align .env.vps polish flag
grep -q '^DICTATION_POLISH_USE_LLM=' .env.vps 2>/dev/null \
  && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' .env.vps \
  || echo 'DICTATION_POLISH_USE_LLM=true' >> .env.vps
grep -q '^DICTATION_POLISH_USE_LLM=' .env 2>/dev/null \
  && sed -i 's/^DICTATION_POLISH_USE_LLM=.*/DICTATION_POLISH_USE_LLM=true/' .env \
  || echo 'DICTATION_POLISH_USE_LLM=true' >> .env

docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --build frontend backend 2>&1 | tail -25
sleep 20
python3 - <<'PY'
from pathlib import Path
p = Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8')
checks = [
    ('no_groq_msg', 'النص جاهز (${from})' not in p and 'Texte prêt (${from})' not in p),
    ('no_mic_whisper', 'يخترع Whisper' not in p and 'Whisper invente' not in p),
    ('no_fidelity_banner', 'تنظيف محلي بدون اختراع' not in p),
    ('auto_polished', 'setPolished(lightCleanDictation(cleaned))' in p),
]
for name, ok in checks:
    print(name, 'OK' if ok else 'FAIL')
PY
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM 2>&1
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
curl -sf -o /dev/null -w 'api:%{http_code}\n' https://lexhub.space/api/health || curl -sf -o /dev/null -w 'api_root:%{http_code}\n' https://lexhub.space/api/ || true
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
