#!/usr/bin/env python3
import paramiko

PASSWORD = "P@s$wiy.O0p"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password=PASSWORD, timeout=60, banner_timeout=120)
_, o, e = c.exec_command(
    "grep -nE 'النص جاهز|تنظيف محلي|يخترع Whisper|Texte prêt' "
    "/opt/sanad/frontend/src/components/redaction/plaidoirie-workspace.tsx "
    "|| echo no_bad_msgs; "
    "docker exec sanad-backend-1 printenv DICTATION_POLISH_USE_LLM; "
    "grep -n 'setPolished(lightCleanDictation' "
    "/opt/sanad/frontend/src/components/redaction/plaidoirie-workspace.tsx | head -3"
)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err.strip():
    print(err[-400:])
c.close()
