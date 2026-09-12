#!/usr/bin/env python3
import os
import paramiko

ROOT = "/opt/sanad"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "51.38.78.23",
    username="root",
    password=os.environ["VPS_SSH_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
sftp = c.open_sftp()
sftp.put(
    r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\docker-compose.lexhub.yml",
    f"{ROOT}/docker-compose.lexhub.yml",
)
sftp.close()
cmd = f"""cd {ROOT}
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d
for i in $(seq 1 60); do curl -sf http://127.0.0.1:8001/health/live >/dev/null && break; sleep 5; done
curl -sf http://127.0.0.1:8001/health/live
docker compose exec -T backend python scripts/seed_test_accounts.py || true
for i in $(seq 1 90); do curl -sf http://127.0.0.1:3000/ >/dev/null && break; sleep 5; done
curl -sf http://127.0.0.1:3000/ >/dev/null
systemctl reload caddy || systemctl restart caddy
curl -sfI https://lexhub.space/ | head -5
echo DEPLOY_OK
"""
_, o, e = c.exec_command(cmd, timeout=3600)
code = o.channel.recv_exit_status()
print(o.read().decode()[-8000:])
err = e.read().decode()
if err:
    print(err[-3000:])
print("exit", code)
c.close()
raise SystemExit(code)
