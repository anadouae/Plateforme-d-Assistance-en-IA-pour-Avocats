#!/usr/bin/env python3
"""Hotfix PDF fonts via Archive + smoke test."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
sftp.put(str(ROOT / "backend/app/services/pdf_export.py"), "/opt/sanad/backend/app/services/pdf_export.py")
sftp.close()
print("uploaded pdf_export.py")

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend 2>&1 | tail -6
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python <<'PY'
from app.services.pdf_export import build_plaidoirie_pdf
b, n = build_plaidoirie_pdf(
    title="مرافعة تجريبية",
    body="أولاً — في الوقائع\n\nنص تجريبي عن القضية 180.\n\nثانياً — في المناقشة\n\nمناقشة قانونية.\n\nلهذه الأسباب\n\n1. القول بما جاء.",
    cabinet_name="Cabinet Démo Atlas",
    lawyer_name="ذ. تجريبي",
    city="الدار البيضاء",
)
print("OK", n, len(b), b[:5])
assert b.startswith(b"%PDF")
assert len(b) > 5000
PY
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr:", err[-1000:])
c.close()
print("DONE")
