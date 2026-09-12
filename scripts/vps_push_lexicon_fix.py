#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
sftp = c.open_sftp()
sftp.put(
    "backend/app/services/arabic_text_fix.py",
    "/opt/sanad/backend/app/services/arabic_text_fix.py",
)
sftp.close()
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -5
sleep 7
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.arabic_text_fix import repair_arabic_stt
from app.services.dictation import polish_dictation
raw = "بسم الله بمديمة دعوة بيضاء لقديت الاتجار بالبشر أمام القادي"
print("lex:", repair_arabic_stt(raw))
p, prov = polish_dictation(raw, language="ar", source="audio")
print("prov:", prov)
print("out:", p[:300])
assert "الله" in repair_arabic_stt(raw)
assert "الالاتجار" not in repair_arabic_stt(raw)
assert prov != "none"
print("OK")
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print("err", err[-600:])
c.close()
