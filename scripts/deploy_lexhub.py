#!/usr/bin/env python3
"""Deploy Sanad to lexhub.space VPS. Requires VPS_SSH_PASSWORD env var."""
from __future__ import annotations

import os
import secrets
import sys
import tarfile
import tempfile
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOST = os.environ.get("VPS_HOST", "51.38.78.23")
USER = os.environ.get("VPS_USER", "root")
PASSWORD = os.environ.get("VPS_SSH_PASSWORD", "")
REMOTE_DIR = "/opt/sanad"
DOMAIN = "lexhub.space"

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".cursor",
    "agent-transcripts",
    "terminals",
    "mcps",
}
SKIP_SUFFIXES = {".pyc", ".ogg", ".wav", ".pptx"}
SKIP_NAMES = {"المعاملات العقارية.pdf", "audio de test en arabe.ogg"}


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    print(f"\n>>> {cmd[:120]}{'…' if len(cmd) > 120 else ''}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if out.strip():
        print(out.strip()[-4000:])
    if err.strip() and code != 0:
        print(err.strip()[-2000:], file=sys.stderr)
    return code, out, err


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip()
    return data


def build_env_vps(local: dict[str, str]) -> str:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        Fernet = None  # type: ignore

    secret = local.get("SECRET_KEY") or secrets.token_urlsafe(48)
    enc = local.get("ENCRYPTION_KEY")
    if not enc and Fernet:
        enc = Fernet.generate_key().decode()

    keys = [
        "GROQ_API_KEY",
        "KIMI_API_KEY",
        "KIMI_BASE_URL",
        "KIMI_MODEL",
        "MISTRAL_API_KEY",
        "MISTRAL_BASE_URL",
        "MISTRAL_MODEL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_MODEL",
        "TOGETHER_API_KEY",
        "TOGETHER_MODEL",
        "SAMBANOVA_API_KEY",
        "SAMBANOVA_MODEL",
        "TAVILY_API_KEY",
        "WEB_SEARCH_PROVIDER",
        "LLM_PROVIDER",
        "LLM_ALLOW_CLOUD_FALLBACK",
        "LLM_USE_FREE_ROUTER",
        "LLM_CHAT_CLOUD_FIRST",
    ]
    lines = [
        "ENVIRONMENT=development",
        "DEBUG=false",
        f"FRONTEND_URL=https://{DOMAIN}",
        f"NEXT_PUBLIC_API_URL=https://{DOMAIN}",
        f"CORS_ORIGINS=https://{DOMAIN},https://www.{DOMAIN}",
        f"SECRET_KEY={secret}",
        f"ENCRYPTION_KEY={enc or ''}",
        "SEED_DEMO_DATA=true",
        "WHISPER_ENABLED=true",
        "WHISPER_MODEL=small",
        "WHISPER_DEVICE=cpu",
        "WHISPER_COMPUTE_TYPE=int8",
        "TURNSTILE_SITE_KEY=1x00000000000000000000AA",
        "TURNSTILE_SECRET_KEY=1x0000000000000000000000000000000AA",
        "CAPTCHA_AFTER_FAILURES=3",
    ]
    for k in keys:
        if local.get(k):
            lines.append(f"{k}={local[k]}")
    return "\n".join(lines) + "\n"


def should_skip(rel: Path) -> bool:
    parts = set(rel.parts)
    if parts & SKIP_DIRS:
        return True
    if rel.name in SKIP_NAMES:
        return True
    return rel.suffix.lower() in SKIP_SUFFIXES


def make_tarball() -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    tmp.close()
    tar_path = Path(tmp.name)
    print(f"Creating archive {tar_path} …")
    with tarfile.open(tar_path, "w:gz") as tar:
        for p in ROOT.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if should_skip(rel):
                continue
            tar.add(p, arcname=str(rel).replace("\\", "/"))
    print(f"Archive size: {tar_path.stat().st_size / 1024 / 1024:.1f} MB")
    return tar_path


def main() -> int:
    if not PASSWORD:
        print("Export VPS_SSH_PASSWORD then rerun.", file=sys.stderr)
        return 1

    local_env = parse_env(ROOT / ".env")
    local_env.update(parse_env(ROOT / "backend" / ".env"))
    env_vps = build_env_vps(local_env)
    tar_path = make_tarball()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST} …")
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)

    install_script = r"""set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg git ufw tar

if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker…"
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

if ! command -v caddy >/dev/null 2>&1; then
  echo "Installing Caddy…"
  apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy
fi

mkdir -p /opt/sanad
"""
    code, _, _ = run(client, install_script, timeout=900)
    if code != 0:
        return code

    sftp = client.open_sftp()
    remote_tar = "/tmp/sanad-deploy.tar.gz"
    print(f"Uploading to {remote_tar} …")
    sftp.put(str(tar_path), remote_tar)
    sftp.close()
    os.unlink(tar_path)

    code, _, _ = run(
        client,
        f"rm -rf {REMOTE_DIR}/* && tar -xzf {remote_tar} -C {REMOTE_DIR} && rm -f {remote_tar}",
        timeout=300,
    )
    if code != 0:
        return code

    sftp = client.open_sftp()
    with sftp.file(f"{REMOTE_DIR}/.env.vps", "w") as f:
        f.write(env_vps)
    with sftp.file("/etc/caddy/Caddyfile", "w") as f:
        f.write((ROOT / "deploy" / "Caddyfile.lexhub").read_text(encoding="utf-8"))
    sftp.close()

    deploy_cmd = f"""
set -e
cd {REMOTE_DIR}
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true
systemctl enable caddy
systemctl reload caddy || systemctl restart caddy
docker compose -f docker-compose.yml -f docker-compose.lexhub.yml --env-file .env.vps up -d --build
echo "Waiting for backend…"
for i in $(seq 1 40); do
  curl -sf http://127.0.0.1:8001/health/live >/dev/null && break
  sleep 5
done
curl -sf http://127.0.0.1:8001/health/live || exit 1
docker compose exec -T backend python scripts/seed_test_accounts.py || true
curl -sf http://127.0.0.1:3000/ >/dev/null || sleep 10
echo DEPLOY_OK
"""
    code, out, _ = run(client, deploy_cmd, timeout=3600)
    client.close()
    if code != 0 or "DEPLOY_OK" not in out:
        print("Deploy failed", file=sys.stderr)
        return code or 1
    print(f"\n✅ Sanad en ligne : https://{DOMAIN}")
    print("Compte démo : demo@sanad.ma / Sanad2026!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
