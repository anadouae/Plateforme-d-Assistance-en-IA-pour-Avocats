#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
_, o, e = c.exec_command(
    "docker exec sanad-backend-1 python -c \""
    "from app.core.config import settings; "
    "k=bool((settings.GROQ_API_KEY or '').strip()); "
    "print('local_only', settings.DICTATION_LOCAL_ONLY); "
    "print('groq_model', settings.GROQ_WHISPER_MODEL); "
    "print('groq_key', k); "
    "print('whisper', settings.WHISPER_MODEL)"
    "\""
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
