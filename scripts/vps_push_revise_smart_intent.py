#!/usr/bin/env python3
"""Deploy smarter revise intent (natural language / typos)."""
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
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart backend frontend 2>&1 | tail -10
sleep 16
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from app.services.plaidoirie_revise import (
    _wants_fill_gaps, _looks_like_complaint_or_point, _thin_sections_in, _SYSTEM,
)
s = "mais tu n a s rien ecrit ici خامساً : /: لهذه الأسباب"
assert _wants_fill_gaps(s)
assert _looks_like_complaint_or_point(s)
assert "INTENTION INTERPRÉTÉE" in _SYSTEM or "COMPRÉHENSION INTELLIGENTE" in _SYSTEM
body = "رابعاً : نص طويل حول النفقة والحضانة ومصلحة المحضون بشكل واضح ومفصل جدا.\nخامساً :\n\nلهذه الأسباب:\n\n"
thin = _thin_sections_in(body)
assert "خامساً" in thin and "لهذه الأسباب" in thin
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
