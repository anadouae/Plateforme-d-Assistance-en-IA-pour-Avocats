#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
_, o, _ = c.exec_command(
    "docker exec sanad-frontend-1 printenv NEXT_PUBLIC_API_URL 2>/dev/null; "
    "docker exec sanad-backend-1 printenv DATABASE_URL FRONTEND_URL ENVIRONMENT 2>/dev/null | sed 's/:[^:@]*@/:***@/'; "
    "docker exec sanad-postgres-1 psql -U sanad -d sanad -c 'SELECT COUNT(*) AS users FROM users;' 2>/dev/null; "
    "curl -sS ipinfo.io/json 2>/dev/null | head -c 400; echo; "
    "docker inspect sanad-postgres-1 --format '{{.HostConfig.Binds}} {{.NetworkSettings.Networks}}' 2>/dev/null | head -c 300"
)
print(o.read().decode(errors="replace"))
c.close()
