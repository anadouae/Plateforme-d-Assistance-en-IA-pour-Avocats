#!/usr/bin/env python3
"""Deploy: identité inline, dictée Whisper fallback, OpenAI prioritaire."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/free_llm_router.py",
    "frontend/src/lib/case-legal.ts",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "mkdir -p /opt/sanad/backend/app/services "
    "/opt/sanad/frontend/src/lib "
    "/opt/sanad/frontend/src/components/cases "
    "/opt/sanad/frontend/src/components/redaction"
)
o.read(); e.read()
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 14
python3 - <<'PY'
from pathlib import Path
ws = Path('frontend/src/components/redaction/plaidoirie-workspace.tsx').read_text(encoding='utf-8')
router = Path('backend/app/services/free_llm_router.py').read_text(encoding='utf-8')
legal = Path('frontend/src/lib/case-legal.ts').read_text(encoding='utf-8')
print('inline_save', 'Enregistrer l’identité sur le dossier' in ws or 'حفظ الهوية على الملف' in ws)
print('no_fiche_btn', 'Fiche dossier complète' not in ws)
print('whisper_fallback', 'recorderOk' in ws and 'Dictée serveur' in ws)
print('openai_prio', 'preferred = "openai"' in router)
print('quality_opts', 'QUALITY_OPTIONS' in legal and 'personne_physique' in legal)
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-600:])
c.close()
print("DONE")
