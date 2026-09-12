#!/usr/bin/env python3
import paramiko
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=60)
_,o,_=c.exec_command("grep -n 'createMediaStreamDestination\\|256_000\\|MediaRecorder(stream' /opt/sanad/frontend/src/hooks/use-whisper-dictation.ts | head -20; ls -la /opt/sanad/frontend/src/hooks/use-whisper-dictation.ts")
print(o.read().decode())
c.close()
