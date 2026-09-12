#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/core/config.py",
    "backend/app/services/free_llm_router.py",
    "backend/app/services/local_llm.py",
    "backend/app/services/cloud_ocr.py",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

# clearer fallback message when LLM down (not OCR blame)
cmd = r"""
cd /opt/sanad
python3 - <<'PY'
from pathlib import Path
p = Path('backend/app/services/agent.py')
t = p.read_text(encoding='utf-8')
old_fr = '''Les modèles IA n'ont pas pu produire de synthèse pour cette pièce "
            "(texte trop pauvre, OCR illisible, ou providers indisponibles).'''
new_fr = '''Les modèles IA n'ont pas pu produire de synthèse pour cette pièce "
            "(service IA saturé ou temporairement indisponible — le texte extrait est conservé).'''
old_ar = '''تعذر على نماذج الذكاء الاصطناعي إعداد تلخيص لهذه القطعة "
            "(نص ضعيف، OCR غير واضح، أو مزود غير متاح).'''
new_ar = '''تعذر على نماذج الذكاء الاصطناعي إعداد تلخيص لهذه القطعة "
            "(خدمة الذكاء الاصطناعي مشغولة مؤقتاً — النص المستخرج محفوظ).'''
n = 0
if old_fr in t:
    t = t.replace(old_fr, new_fr); n += 1
if old_ar in t:
    t = t.replace(old_ar, new_ar); n += 1
p.write_text(t, encoding='utf-8')
print('fallback_msg', n)
PY
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -12
sleep 8
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
print("DONE")
