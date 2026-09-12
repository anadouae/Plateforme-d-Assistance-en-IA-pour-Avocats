#!/usr/bin/env python3
"""Deploy Arabic bidi display fix (frontend)."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
FILES = [
    "frontend/src/lib/arabic-bidi.ts",
    "frontend/src/app/globals.css",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/redaction/document-workspace.tsx",
    "frontend/src/components/redaction/plea-assist-panel.tsx",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
for rel in FILES:
    sftp.put(str(ROOT / rel), f"/opt/sanad/{rel}")
    print("ok", rel)
sftp.close()

cmd = """
cd /opt/sanad
CID=$(docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps -q frontend)
for f in frontend/src/lib/arabic-bidi.ts frontend/src/app/globals.css frontend/src/styles/sanad-ui.css frontend/src/components/redaction/plaidoirie-workspace.tsx frontend/src/components/redaction/document-workspace.tsx frontend/src/components/redaction/plea-assist-panel.tsx; do
  docker cp /opt/sanad/$f ${CID}:/app/$f
done
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend 2>&1 | tail -4
sleep 10
curl -sf -o /dev/null -w 'web:%{http_code}\\n' https://lexhub.space/
"""
_, o, e = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("err", err[-500:])
c.close()
print("DONE")
