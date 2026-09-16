#!/usr/bin/env python3
"""Confirm VPS admin-shell has no Image import leftover; show file head."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
cmd = r"""
cd /opt/sanad
echo '=== Image refs ==='
grep -n 'Image\|adminPlatform\|from \"next/image\"' frontend/src/components/layout/admin-shell.tsx | head -20
echo '=== page admin t ==='
grep -n 'adminPlatform\|if (!t)' frontend/src/app/admin/page.tsx | head -15
# Force recompile by touching
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T frontend sh -c 'rm -rf /app/.next; echo next_wiped'
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml restart frontend
sleep 22
curl -s https://lexhub.space/admin 2>/dev/null | tr '\n' ' ' | head -c 400; echo
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs frontend --tail 25 2>&1 | tail -20
"""
_, o, e = c.exec_command(cmd, timeout=240)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-500:])
c.close()
