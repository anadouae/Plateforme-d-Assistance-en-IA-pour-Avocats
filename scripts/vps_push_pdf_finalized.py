#!/usr/bin/env python3
"""Deploy PDF RTL/logo fix + finalized status + hide export checks."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/pdf_export.py",
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/api/plaidoirie_templates.py",
    "backend/app/api/workspace.py",
    "backend/app/schemas/__init__.py",
    "backend/app/models/__init__.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/lib/api.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -12
sleep 18
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.plaidoirie_layout import sanitize_export_text, prepare_plaidoirie_blocks
from app.services.pdf_export import _para_html, _block_kind

s = sanitize_export_text("المدعية : فاطمة\n[] المدعى عليه : خالد\n• حدث في 2024")
assert "[]" not in s
assert "□" not in s
blocks = prepare_plaidoirie_blocks("أولاً : في الشكل\nنص طويل.\n– نقطة أولى\nثانياً : في الموضوع")
assert any("أولاً" in b for b in blocks)
html = _para_html("أولاً : في الشكل", "sec")
assert 'dir="rtl"' in html and "text-align:right" in html
print("SMOKE_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
