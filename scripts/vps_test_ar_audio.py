#!/usr/bin/env python3
"""Upload Arabic test audio to VPS and run Groq transcription."""
from pathlib import Path
import paramiko

PASSWORD = "P@s$wiy.O0p"
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "audio de test en arabe.ogg"
WAV = ROOT / "scripts" / "fixtures" / "sanad-test-audio.wav"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
sftp = c.open_sftp()
remote_ogg = "/tmp/sanad-ar-test.ogg"
remote_wav = "/tmp/sanad-ar-test.wav"
if LOCAL.exists():
    sftp.put(str(LOCAL), remote_ogg)
    print("uploaded ogg", LOCAL.stat().st_size)
if WAV.exists():
    sftp.put(str(WAV), remote_wav)
    print("uploaded wav", WAV.stat().st_size)
sftp.close()

cmd = r"""
cd /opt/sanad
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from pathlib import Path
from app.services.whisper_stt import transcribe_audio_bytes, _transcribe_groq

for name, path in [("ogg", "/tmp/sanad-ar-test.ogg"), ("wav", "/tmp/sanad-ar-test.wav")]:
    p = Path(path)
    # files are on host; copy into container via stdin not available — read from mounted? 
    print(name, "exists_in_container", p.exists())
PY
# copy into container
docker cp /tmp/sanad-ar-test.ogg sanad-backend-1:/tmp/sanad-ar-test.ogg 2>/dev/null || true
docker cp /tmp/sanad-ar-test.wav sanad-backend-1:/tmp/sanad-ar-test.wav 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml exec -T backend python - <<'PY'
from pathlib import Path
from app.services.whisper_stt import transcribe_audio_bytes

for label, path in [("ogg", "/tmp/sanad-ar-test.ogg"), ("wav", "/tmp/sanad-ar-test.wav")]:
    p = Path(path)
    if not p.exists():
        print(label, "MISSING")
        continue
    data = p.read_bytes()
    text, prov = transcribe_audio_bytes(data, filename=p.name, language="ar")
    print("===", label, "prov=", prov, "chars=", len(text or ""))
    print(text)
    print("---")
PY
echo '=== RECENT USER STT ==='
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml logs backend --since 20m 2>&1 | grep -iE 'preview=|chrome|groq-primary|chars=' | tail -20
"""
_, o, e = c.exec_command(cmd, timeout=180)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print("ERR", err[-1500:])
c.close()
