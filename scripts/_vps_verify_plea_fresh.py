#!/usr/bin/env python3
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("51.38.78.23", username="root", password="P@s$wiy.O0p", timeout=40, banner_timeout=60)


def run(cmd, timeout=90):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    print((o.read().decode(errors="replace") + e.read().decode(errors="replace"))[-3000:])


run("grep -n 'looks_like_nonsense\\|__NONSENSE__' /opt/sanad/backend/app/services/dictation.py | head")
run("grep -n 'fresh=1\\|hasMeaningfulPleaSession' /opt/sanad/frontend/src/app/redaction/new/page.tsx | head")
run("curl -sS -m 20 -o /dev/null -w 'new:%{http_code} t=%{time_total}\\n' --resolve lexhub.space:443:127.0.0.1 https://lexhub.space/redaction/new")
run("docker exec sanad-backend-1 python -c \"from app.services.dictation import looks_like_nonsense, polish_dictation; print(looks_like_nonsense('k;k;l;'), polish_dictation('k;k;l;', language='ar')[1])\"")
c.close()
