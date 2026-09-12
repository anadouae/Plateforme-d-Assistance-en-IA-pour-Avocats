#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/extraction.py",
    "backend/app/services/agent.py",
    "frontend/src/components/ai/synthesis-panel.tsx",
]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()
cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend 2>&1 | tail -8
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -3
sleep 9
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.extraction import _looks_like_broken_arabic_snippet
bad='ومنعاً للحقوق صيانةً برمتها المسطرة بطلان به الإخلال على ويترتب مخالفته، على الاتفاق يجوز لا'
good='يعتبر البيع الجبري مسطرة دقيقة ويترتب على مخالفتها البطلان عند الإخلال بالضمانات.'
print('reject_reversed', _looks_like_broken_arabic_snippet(bad))
print('keep_good', not _looks_like_broken_arabic_snippet(good))
print('reject_question', _looks_like_broken_arabic_snippet('كيف تدار جلسة المزاد العلني من الناحية العملية؟'))
PY
"""
_, o, e = c.exec_command(cmd, timeout=150)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
print("DONE")
