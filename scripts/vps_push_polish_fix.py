#!/usr/bin/env python3
"""Push Arabic polish fix + recreate backend/frontend."""
import json
import paramiko

FILES = [
    "backend/app/core/config.py",
    "backend/app/services/free_llm_router.py",
    "backend/app/services/dictation.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/api/dictation.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "docker-compose.lexhub.yml",
]
REMOTE = "/opt/sanad"
HOST = "51.38.78.23"
PASS = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASS, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(rel, f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 && sleep 8 && "
    f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1",
    timeout=180,
)
print(o.read().decode(errors="replace")[-1500:])
err = e.read().decode(errors="replace")[-500:]
if err:
    print("stderr", err)

# Smoke polish (login optional — try internal python call)
smoke = r"""
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation import polish_dictation
from app.services.arabic_text_fix import repair_arabic_stt
raw = "بسم الله بمديمة دعوة بيضاء لقديت الاتجار بالبشر أمام القادي"
print("lexicon:", repair_arabic_stt(raw))
polished, prov = polish_dictation(raw, language="ar", source="audio")
print("provider:", prov)
print("polished:", (polished or "")[:400])
assert prov != "none", "polish still degraded"
assert "الدار البيضاء" in polished or "البيضاء" in polished or "مدينة" in polished
print("SMOKE_OK")
PY
"""
_, o2, e2 = c.exec_command(f"cd {REMOTE} && {smoke}", timeout=120)
out2 = o2.read().decode(errors="replace")
err2 = e2.read().decode(errors="replace")
print(out2)
if err2:
    print("smoke_err", err2[-800:])
c.close()
print("done")
