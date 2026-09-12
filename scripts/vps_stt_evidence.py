#!/usr/bin/env python3
"""Fetch latest STT previews + dump one recent request path."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=120)
cmd = r"""
cd /opt/sanad
echo '=== LAST 20 STT LINES ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --since 45m 2>&1 | grep -iE 'STT|groq|transcrib|polish|preview' | tail -40

echo '=== FRONTEND BUNDLE AGE ==='
ls -la frontend/src/hooks/use-whisper-dictation.ts frontend/src/components/redaction/plaidoirie-workspace.tsx
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T frontend sh -c 'ls -la /app/src/hooks/use-whisper-dictation.ts 2>/dev/null; grep -c createMediaStreamDestination /app/src/hooks/use-whisper-dictation.ts 2>/dev/null; grep -c "256_000" /app/src/hooks/use-whisper-dictation.ts 2>/dev/null'

echo '=== POLISH MODE ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend printenv DICTATION_POLISH_USE_LLM DICTATION_STT_PREFER_GROQ DICTATION_LOCAL_ONLY
"""
_, o, e = c.exec_command(cmd, timeout=90)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("ERR", err[-1000:])
c.close()
