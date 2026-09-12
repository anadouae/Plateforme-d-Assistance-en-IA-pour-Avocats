#!/usr/bin/env python3
"""Deploy PDF RTL, revise expand, daily quota popups. No --build."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/pdf_export.py",
    "backend/app/services/plaidoirie_layout.py",
    "backend/app/services/plaidoirie_postprocess.py",
    "backend/app/services/plaidoirie_revise.py",
    "backend/app/services/billing.py",
    "backend/app/core/rate_limit.py",
    "frontend/src/lib/api.ts",
    "frontend/src/store/billing-credits.ts",
    "frontend/src/components/billing/credit-spend-toast.tsx",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/styles/sanad-ui.css",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        raise SystemExit(f"missing: {rel}")
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

cmd = r"""
set -e
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml up -d --force-recreate backend frontend 2>&1 | tail -25
sleep 12
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python -c "from app.services.pdf_export import build_plaidoirie_pdf; from app.services.plaidoirie_revise import _wants_expand; from app.core.rate_limit import get_cabinet_ai_daily_used; assert _wants_expand('develoope d eplsu cette partie'); pdf, name = build_plaidoirie_pdf(title='مرافعة موسعة في قضية نفقة وحضانة', body='أولاً : تحديد الأطراف: السيدة فاطمة.\nثانياً : في الشكل: نحن أمام المحكمة.\nثالثاً : في الوقائع: 1. انعقد الزواج في 15 يونيو 2020. 2. رزق الطرفان بابنيهما يوسف. 3. توقف المدعى عليه عن أداء النفقة.', cabinet_name='Cabinet Demo Atlas', cabinet_name_ar='مكتب أطلس', lawyer_name='دعاء العدل', city='Casablanca', case_reference='WV-2026-0014'); print('pdf', name, len(pdf), pdf[:4])"
curl -s -o /dev/null -w 'home=%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=420)
print(o.read().decode(errors="replace")[-8000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr", err[-2000:])
c.close()
print("done")
