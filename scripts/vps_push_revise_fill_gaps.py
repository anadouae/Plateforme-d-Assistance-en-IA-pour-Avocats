#!/usr/bin/env python3
"""Deploy revise fill-gaps (خامساً / لهذه الأسباب) + honest UI."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "backend/app/services/plaidoirie_revise.py",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
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
from app.services.plaidoirie_revise import (
    _wants_fill_gaps, _thin_sections_in, _is_section_thin, _markers_mentioned,
)
s = "mais tu n a s rien ecrit ici خامساً : /: لهذه الأسباب"
assert _wants_fill_gaps(s), "fill detect"
assert "خامساً" in _markers_mentioned(s)
body = "رابعاً : نص طويل بما فيه الكفاية هنا حول النفقة والحضانة.\nخامساً :\n\nلهذه الأسباب:\n\n"
assert "خامساً" in _thin_sections_in(body)
assert _is_section_thin(body, "خامساً")
assert _is_section_thin(body, "لهذه الأسباب")
filled = body.replace("خامساً :\n\n", "خامساً :\nحيث إن مصلحة المحضون تقتضي كذا وكذا وكذا وكذا.\n\n")
assert not _is_section_thin(filled, "خامساً")
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
