#!/usr/bin/env python3
import paramiko
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/core/config.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/arabic_text_fix.py",
    "backend/app/services/stt_quality.py",
    "frontend/src/hooks/use-speech-input.ts",
    "frontend/src/hooks/use-whisper-dictation.ts",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend 2>&1 && "
    f"docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 && "
    f"sleep 6 && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend python -c \""
    f"from app.core.config import settings; from app.services.arabic_text_fix import repair_arabic_stt; "
    f"print('CHUNK', settings.WHISPER_CHUNK_ENABLED); "
    f"raw='ان الرفع الاتية ان المرافعة الاتية التي نحن بصدد اعدادها تخص جريمة من جرائم بيع المخدرات جاء المملكة المغربية التي تم دتها المدعو حميدو والتهنية ان الرفع الاتية ان المرافعة الاتية التي نحن بصدد اعدادها تخص جريمة من جرائم بيع المخدرات جاء المملكة المغربية التي تم دتها المدعو حميدو والتهنية ابن هنية'; "
    f"print(repair_arabic_stt(raw))"
    f"\" 2>&1",
    timeout=180,
)
print(o.read().decode(errors="replace")[-2000:])
c.close()
print("done")
