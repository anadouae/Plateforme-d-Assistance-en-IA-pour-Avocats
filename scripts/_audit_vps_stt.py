#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60, banner_timeout=90)
cmds = r"""
echo '=== free -h ==='; free -h
echo '=== nproc ==='; nproc
echo '=== lscpu ==='; lscpu | egrep 'Model name|CPU\(s\)|Thread|Core|Architecture'
echo '=== df -h / ==='; df -h /
echo '=== swapon ==='; swapon --show || true
echo '=== uptime ==='; uptime
echo '=== docker ps ==='; docker ps --format 'table {{.Names}}\t{{.Status}}'
echo '=== docker stats ==='; docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'
echo '=== STT env ==='
docker exec sanad-backend-1 python -c "from app.core.config import settings; print('DICTATION_LOCAL_ONLY', settings.DICTATION_LOCAL_ONLY); print('WHISPER_MODEL', settings.WHISPER_MODEL); print('WHISPER_DEVICE', settings.WHISPER_DEVICE); print('WHISPER_COMPUTE', settings.WHISPER_COMPUTE_TYPE); print('WHISPER_TIMEOUT', settings.WHISPER_TIMEOUT_SEC); print('GROQ_KEY', bool((settings.GROQ_API_KEY or '').strip()))"
"""
_, o, e = c.exec_command(cmds, timeout=120)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("STDERR:", err[-800:])
c.close()
