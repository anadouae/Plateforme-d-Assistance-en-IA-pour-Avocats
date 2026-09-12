from pathlib import Path
import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
REMOTE = "/opt/sanad"
FILES = [
    "backend/app/services/billing.py",
    "backend/app/api/billing.py",
    "backend/app/api/auth.py",
    "backend/app/api/realtime_ws.py",
    "backend/app/api/team.py",
    "backend/app/api/settings.py",
    "backend/app/core/rate_limit.py",
    "backend/app/main.py",
    "frontend/src/app/tarifs/page.tsx",
    "frontend/src/app/join/page.tsx",
    "frontend/src/app/redaction/page.tsx",
    "frontend/src/lib/roles.ts",
    "frontend/src/components/settings/billing-panel.tsx",
    "frontend/src/components/billing/subscription-banner.tsx",
    "frontend/src/styles/sanad-ui.css",
]

# empty state CTA lawyer only
rp = ROOT / "frontend/src/app/redaction/page.tsx"
t = rp.read_text(encoding="utf-8")
old = """      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/50 p-8 text-center text-sm text-[var(--ink-soft)]">
          {labels.empty}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => {
            const validated = d.status === "validated";"""
new = """      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/50 p-8 text-center text-sm text-[var(--ink-soft)]">
          <p>{labels.empty}</p>
          <button type="button" className="chip-btn primary mt-4 inline-flex items-center gap-2" onClick={openNew}>
            <Mic className="h-4 w-4" />
            {labels.new}
          </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => {
            const validated = d.status === "validated";"""
if old in t:
    rp.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("empty state ok")
else:
    print("empty state pattern missing")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="root", password=PASSWORD, timeout=60, banner_timeout=90)
sftp = c.open_sftp()
for rel in FILES:
    local = ROOT / rel
    if not local.exists():
        print("SKIP", rel)
        continue
    sftp.put(str(local), f"{REMOTE}/{rel}")
    print("ok", rel)
sftp.close()
_, o, e = c.exec_command(
    f"cd {REMOTE} && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
    f"up -d --force-recreate backend frontend 2>&1 | tail -30",
    timeout=360,
)
print((o.read() + e.read()).decode(errors="replace")[-3500:])
print("exit", o.channel.recv_exit_status())
c.close()
print("done")
