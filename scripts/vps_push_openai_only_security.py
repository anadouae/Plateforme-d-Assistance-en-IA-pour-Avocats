#!/usr/bin/env python3
"""Deploy OpenAI-only + Caddy security/cache headers."""
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/core/config.py",
    "backend/app/services/whisper_stt.py",
    "backend/app/services/free_llm_router.py",
    "docker-compose.lexhub.yml",
    "deploy/Caddyfile.lexhub",
    "frontend/src/components/brand/sanad-logo.tsx",
]

ENV_KEYS = {
    "OPENAI_MODEL": "gpt-4o",
    "LLM_FORCE_OPENAI": "true",
    "LLM_OPENAI_STRICT": "true",
    "LLM_USE_FREE_ROUTER": "false",
    "DICTATION_OPENAI_ONLY": "true",
    "DICTATION_STT_PREFER_GROQ": "false",
    "WHISPER_ENABLED": "false",
    "DICTATION_POLISH_USE_LLM": "true",
    "OPENAI_WHISPER_MODEL": "whisper-1",
}

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    remote = f"{REMOTE}/{rel}"
    _, o, _ = c.exec_command(f"mkdir -p $(dirname {remote})")
    o.channel.recv_exit_status()
    sftp.put(str(local), remote)
    print("ok", rel)
sftp.close()

# Patch env files
lines = ["cd /opt/sanad"]
for f in (".env", ".env.vps"):
    for k, v in ENV_KEYS.items():
        lines.append(
            f'if [ -f {f} ]; then '
            f'grep -q "^{k}=" {f} && sed -i "s/^{k}=.*/{k}={v}/" {f} || echo "{k}={v}" >> {f}; '
            f'fi'
        )
lines.append("grep -E 'OPENAI_MODEL|LLM_OPENAI_STRICT|DICTATION_OPENAI|WHISPER_ENABLED' .env.vps | head -20")
lines.append(
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    "up -d --force-recreate backend frontend 2>&1 | tail -25"
)
lines.append(
    "if [ -f /etc/caddy/Caddyfile ]; then cp deploy/Caddyfile.lexhub /etc/caddy/Caddyfile.lexhub.bak 2>/dev/null; "
    "cp deploy/Caddyfile.lexhub /etc/caddy/Caddyfile 2>/dev/null || true; fi"
)
lines.append(
    "if command -v caddy >/dev/null; then "
    "cp deploy/Caddyfile.lexhub /opt/sanad/Caddyfile 2>/dev/null; "
    "systemctl reload caddy 2>&1 || caddy reload --config /etc/caddy/Caddyfile 2>&1 || "
    "docker exec caddy caddy reload --config /etc/caddy/Caddyfile 2>&1 || true; fi"
)
lines.append("sleep 4")
lines.append(
    "docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend "
    "python -c \"from app.core.config import settings; "
    "print('MODEL', settings.OPENAI_MODEL); "
    "print('STRICT', settings.LLM_OPENAI_STRICT); "
    "print('OPENAI_ONLY_STT', settings.DICTATION_OPENAI_ONLY); "
    "print('WHISPER_LOCAL', settings.WHISPER_ENABLED); "
    "print('GROQ_PREF', settings.DICTATION_STT_PREFER_GROQ)\""
)

_, o, e = c.exec_command("\n".join(lines), timeout=500)
print(o.read().decode(errors="replace")[-6000:])
err = e.read().decode(errors="replace")
if err.strip():
    print("stderr:", err[-2000:])
c.close()
print("done")
