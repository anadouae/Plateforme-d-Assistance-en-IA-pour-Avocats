#!/usr/bin/env python3
"""Verify adminPlatform is exported from bundled translations on VPS."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
# quick node check: extract that adminPlatform exists in source
node -e "
const fs=require('fs');
const s=fs.readFileSync('frontend/src/lib/i18n/translations.ts','utf8');
const fr=s.indexOf('adminPlatform');
const ar=s.lastIndexOf('adminPlatform');
console.log('fr', fr, 'ar', ar);
"
# hit admin and show last errors
curl -sI https://lexhub.space/admin | head -5
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs frontend --tail 40 2>&1 | grep -iE 'error|Error|TypeError|adminPlatform|Cannot' | tail -20
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-400:])
c.close()
