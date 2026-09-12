#!/usr/bin/env python3
import time
import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"


def connect(retries=5):
    last = None
    for i in range(retries):
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            c.connect(
                HOST,
                username="root",
                password=PASSWORD,
                timeout=40,
                banner_timeout=60,
                auth_timeout=40,
            )
            return c
        except Exception as exc:
            last = exc
            print(f"ssh fail {i+1}/{retries}: {exc}")
            time.sleep(8)
    raise last


def run(c, cmd, timeout=180):
    print(">>", cmd[:240])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    text = (out or "") + (("\n" + err) if err.strip() else "")
    print(text[-6000:] if text else "(empty)")
    print("exit", code)
    return code, text


def main() -> int:
    c = connect()
    run(c, "uptime; free -h | head -3; df -h / | tail -1")
    run(
        c,
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml ps -a",
        timeout=90,
    )
    run(c, "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | head -40", timeout=60)
    run(c, "ss -tlnp | grep -E ':80|:443|:3000|:8000|:8001' || netstat -tlnp | grep -E ':80|:443|:3000|:8001'", timeout=40)
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
