#!/usr/bin/env python3
"""Diagnose and fix dictation STT on lexhub VPS."""
import paramiko

HOST = "51.38.78.23"
PASS = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASS, timeout=60, banner_timeout=90)

def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    return out, err

print("=== containers ===")
out, _ = run(f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps 2>&1")
print(out[-1500:])

print("=== backend logs (whisper/dictation/oom) ===")
out, _ = run(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"logs backend --tail 120 2>&1 | grep -iE 'whisper|dictation|oom|killed|error|traceback|memory|503|transcrib' || true"
)
print(out[-2500:] or "(no matches)")

print("=== env whisper ===")
out, _ = run(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend printenv | grep -iE 'WHISPER|DICTATION|GROQ' 2>&1"
)
print(out)

print("=== whisper status via python ===")
out, err = run(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"exec -T backend python -c \"from app.services.whisper_stt import whisper_status,_get_model; "
    f"print(whisper_status()); m=_get_model(); print('model', type(m).__name__ if m else None)\" 2>&1",
    timeout=180,
)
print(out)
print(err[-500:] if err else "")

print("=== free mem ===")
out, _ = run("free -h; df -h / | tail -1")
print(out)

c.close()
