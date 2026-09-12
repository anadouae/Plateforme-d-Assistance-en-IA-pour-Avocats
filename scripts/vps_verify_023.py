#!/usr/bin/env python3
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"


def main() -> int:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    cmds = [
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T backend alembic current 2>&1",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T backend python -c \"from app.models import AgendaEvent; "
        "print('has_col', hasattr(AgendaEvent, 'reminder_48h_sent_at'))\" 2>&1",
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "exec -T postgres psql -U sanad -d sanad -c \"\\d agenda_events\" 2>&1 | grep -i reminder || true",
        "curl -sS http://127.0.0.1:8001/health/live 2>&1",
    ]
    for cmd in cmds:
        print(">>>", cmd[:120])
        _, o, e = client.exec_command(cmd, timeout=120)
        print(o.read().decode(errors="replace"))
        err = e.read().decode(errors="replace")
        if err.strip():
            print(err[:500])
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
