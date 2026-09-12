#!/usr/bin/env python3
"""Push correction ه→ة (Chrome STT) frontend + backend."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/arabic_text_fix.py",
    "frontend/src/hooks/use-speech-input.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()

cmd = f"""
cd {REMOTE}
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -5
sleep 10
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.arabic_text_fix import repair_arabic_stt
raw = "في هذه المرافعه جريمه سيده سنه متورطه مجموعه الدعاره المغربيه والدستوريه نقطه الاهميه"
out = repair_arabic_stt(raw)
print(out)
assert "هذه" in out and "هذة" not in out
assert "المرافعة" in out
assert "جريمة" in out
assert "سيدة" in out
assert "سنة" in out
assert "متورطة" in out
assert "مجموعة" in out
assert "الدعارة" in out
assert "المغربية" in out
assert "والدستورية" in out or "الدستورية" in out
assert "نقطة" in out
assert "الأهمية" in out
print("TEH_OK")
PY
curl -sf -o /dev/null -w 'web:%{{http_code}}\\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
