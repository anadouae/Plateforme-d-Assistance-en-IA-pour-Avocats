#!/usr/bin/env python3
"""Deploy Cursor-style invoices + real PDF download."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
    "backend/app/assets/logo-lexhub-cube.png",
    "frontend/src/components/billing/invoices-list.tsx",
    "frontend/src/lib/api.ts",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
# ensure assets dir
try:
    sftp.stat("/opt/sanad/backend/app/assets")
except OSError:
    sftp.mkdir("/opt/sanad/backend/app/assets")
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("MISSING", rel)
        continue
    sftp.put(str(local), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -14
sleep 22
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from datetime import datetime, timezone
from app.services.billing import build_invoice_pdf_bytes, render_cursor_invoice_html
b = build_invoice_pdf_bytes(
    number="LH-SMOKE",
    issued_at=datetime.now(timezone.utc),
    cabinet_name="Cabinet Demo",
    city="Rabat",
    plan_name="Cabinet",
    period_label="2026-09",
    amount_mad=1490,
    billing_cycle="monthly",
    status="paid",
)
h = render_cursor_invoice_html(
    number="LH-SMOKE",
    issued_at=datetime.now(timezone.utc),
    cabinet_name="Cabinet Demo",
    plan_name="Cabinet",
    amount_mad=1490,
    billing_cycle="monthly",
    status="paid",
)
print("pdf", len(b), b[:4], "html", "amount-due" in h, "logo" in h)
PY
"""
_, o, e = c.exec_command(cmd, timeout=360)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-800:])
c.close()
print("DONE")
