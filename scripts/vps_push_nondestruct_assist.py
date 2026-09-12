#!/usr/bin/env python3
"""Deploy non-destructive assist panel (diff / vars / structure / laws)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/dictation_assist.py",
    "backend/app/api/dictation.py",
    "backend/app/services/dictation.py",
    "backend/app/services/plaidoirie_prompt.py",
    "frontend/src/lib/api.ts",
    "frontend/src/components/redaction/plea-assist-panel.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/lib/case-domains.ts",
    "frontend/src/lib/plaidoirie-templates.ts",
    "frontend/src/components/redaction/template-picker.tsx",
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -8
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.dictation_assist import build_assist_payload
from app.services.dictation import polish_dictation

raw = (
    "ان المرافعة التي نحن بصدد القائها سيدي الرئيس تخص قضية اتجار بالمخدرات "
    "ملف رقم 125 تاريخ الجلسة 15 يوليوز 2026 ضحى بنت ليلى نلتمس تعويضا"
)
pol, prov = polish_dictation(raw, language="ar")
assist = build_assist_payload(raw, pol)
assert assist["variables"], assist
assert any(v["kind"] == "case_number" for v in assist["variables"]), assist["variables"]
assert assist["edits"] or "إن" in pol, assist["edits"]
assert assist["structure_hints"] or assist["law_suggestions"]
print("provider", prov)
print("edits", len(assist["edits"]), assist["edits"][:3])
print("vars", [v["value"] for v in assist["variables"]])
print("struct", len(assist["structure_hints"]))
print("laws", [s["code_fr"] for s in assist["law_suggestions"]])
print("SMOKE_ASSIST_OK")
PY
curl -sf -o /dev/null -w 'web:%{http_code}\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=300)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-1200:])
c.close()
print("DONE")
