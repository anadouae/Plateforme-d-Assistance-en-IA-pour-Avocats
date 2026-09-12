#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=45)
_, o, e = c.exec_command(
    "cd /opt/sanad && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "python -c 'from app.core.config import settings; k=settings.ENCRYPTION_KEY or \"\"; print(\"be\", bool(k), repr(k[:10]), settings.USE_MINIO)' && "
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T celery-worker "
    "python -c 'from app.core.config import settings; k=settings.ENCRYPTION_KEY or \"\"; print(\"cw\", bool(k), repr(k[:10]))'",
    timeout=60,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
_, o2, e2 = c.exec_command(
    "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "python -c \"from app.core.database import SessionLocal; from app.models import Document; "
    "db=SessionLocal(); rows=db.query(Document).order_by(Document.created_at.desc()).limit(6).all(); "
    "[print(d.status.value if hasattr(d.status,'value') else d.status, (d.original_name or '')[:50], (d.error_message or '')[:90], d.file_size) for d in rows]; db.close()\"",
    timeout=60,
)
print(o2.read().decode(errors="replace"))
print(e2.read().decode(errors="replace"))
c.close()
