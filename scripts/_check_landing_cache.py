#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=45)
_, o, e = c.exec_command(
    """
cd /opt/sanad
echo '=== ps ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps 2>&1 | head -25
echo '=== headers ==='
curl -sI https://lexhub.space/ | head -30
echo '=== home strings on disk ==='
grep -E 'Du dossier|Deux gestes|LEGALTECH|hero-desk' frontend/src/components/home/home-page-content.tsx frontend/src/lib/i18n/translations.ts 2>/dev/null | head -25
echo '=== frontend cmd ==='
docker inspect sanad-frontend-1 --format '{{.Config.Cmd}} {{.Args}}' 2>/dev/null
echo '=== next cache ==='
du -sh frontend/.next 2>/dev/null; ls frontend/.next 2>/dev/null | head
""",
    timeout=60,
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-1500:])
c.close()
