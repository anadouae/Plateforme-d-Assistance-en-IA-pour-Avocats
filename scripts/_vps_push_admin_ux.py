#!/usr/bin/env python3
from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"

FILES = [
    "backend/app/api/deps.py",
    "backend/app/api/documents.py",
    "backend/app/api/cases.py",
    "backend/app/api/notifications.py",
    "backend/app/schemas/__init__.py",
    "backend/app/services/extraction.py",
    "backend/app/services/dictation.py",
    "backend/app/services/agent.py",
    "backend/app/services/cle_de_barre.py",
    "frontend/src/lib/ownership.ts",
    "frontend/src/lib/api.ts",
    "frontend/src/lib/plea-session.ts",
    "frontend/src/components/documents/document-preview-modal.tsx",
    "frontend/src/components/layout/app-sidebar.tsx",
    "frontend/src/styles/sanad-ui.css",
    "frontend/src/app/cases/page.tsx",
    "frontend/src/app/cases/[id]/page.tsx",
    "frontend/src/app/documents/page.tsx",
    "frontend/src/app/documents/[id]/page.tsx",
    "frontend/src/components/settings/team-panel.tsx",
    "frontend/src/components/layout/topbar-action-icons.tsx",
    "frontend/src/components/redaction/plaidoirie-workspace.tsx",
    "frontend/src/components/cases/new-case-modal.tsx",
    "frontend/src/app/admin/plans/page.tsx",
    "frontend/src/components/layout/admin-shell.tsx",
    "frontend/src/app/admin/logs/page.tsx",
    "frontend/src/app/agenda/page.tsx",
]


def run(c, cmd, timeout=900):
    print(">>", cmd[:220])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if out.strip():
        print(out[-5000:])
    if err.strip():
        print("stderr:", err[-2000:])
    print("exit", code)
    return code


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
    sftp = c.open_sftp()
    for rel in FILES:
        local = ROOT / rel
        if not local.exists():
            raise SystemExit(f"missing {rel}")
        remote = f"{REMOTE}/{rel}"
        parent = str(Path(remote).parent).replace("\\", "/")
        _, o, _ = c.exec_command(f"mkdir -p {parent}")
        o.channel.recv_exit_status()
        sftp.put(str(local), remote)
        print("ok", rel)
    sftp.close()
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "up -d --build backend frontend celery-worker 2>&1 | tail -80",
    )
    run(
        c,
        f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "restart backend frontend celery-worker 2>&1 | tail -20",
        timeout=180,
    )
    run(c, "sleep 15 && curl -fsS -o /dev/null -w '%{http_code}' https://lexhub.space/", timeout=120)
    c.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
