#!/usr/bin/env python3
"""Tunnel Adminer: http://127.0.0.1:8088  — garder cette fenêtre ouverte."""
from __future__ import annotations

import select
import socket
import sys
import threading
import time

import paramiko

HOST = "51.38.78.23"
PASSWORD = "P@s$wiy.O0p"
LOCAL_PORT = 8088
REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 8088


def forward(chan, sock):
    try:
        while True:
            r, _, _ = select.select([sock, chan], [], [], 60)
            if not r:
                continue
            if sock in r:
                data = sock.recv(65535)
                if not data:
                    break
                chan.sendall(data)
            if chan in r:
                data = chan.recv(65535)
                if not data:
                    break
                sock.sendall(data)
    except Exception:
        pass
    finally:
        try:
            chan.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass


def main() -> int:
    print("Connexion au VPS…", flush=True)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            HOST,
            username="root",
            password=PASSWORD,
            timeout=60,
            banner_timeout=120,
            allow_agent=False,
            look_for_keys=False,
        )
    except Exception as exc:
        print("ECHEC SSH:", exc, flush=True)
        return 1

    # Ensure Adminer is up on VPS
    _, o, _ = client.exec_command(
        "cd /opt/sanad && docker compose -f docker-compose.yml -f docker-compose.lexhub.yml "
        "up -d adminer >/dev/null 2>&1; curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8088/",
        timeout=90,
    )
    code = o.read().decode(errors="replace").strip()
    print(f"Adminer sur serveur: HTTP {code}", flush=True)
    if code != "200":
        print("Adminer ne répond pas sur le VPS. Arrêt.", flush=True)
        client.close()
        return 1

    transport = client.get_transport()
    assert transport is not None
    transport.set_keepalive(30)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", LOCAL_PORT))
    except OSError as exc:
        print(f"Port {LOCAL_PORT} déjà pris: {exc}", flush=True)
        print("Fermez l'ancien tunnel, puis relancez.", flush=True)
        client.close()
        return 1
    server.listen(50)

    print("", flush=True)
    print("=" * 62, flush=True)
    print("  Tunnel SSH actif sur http://127.0.0.1:8088", flush=True)
    print("=" * 62, flush=True)
    print("  Étape 2 : Ouvrez votre navigateur (Chrome ou Edge) sur :", flush=True)
    print("  http://127.0.0.1:8088", flush=True)
    print("-" * 62, flush=True)
    print("  Étape 3 : Renseignez les identifiants SQL stricts :", flush=True)
    print("  • Système      : PostgreSQL", flush=True)
    print("  • Serveur      : postgres", flush=True)
    print("  • Utilisateur  : lexhub", flush=True)
    print("  • Mot de passe : LhPg-gGhAymhq7AnfnrlWCEdvsloQ", flush=True)
    print("  • Base         : lexhub", flush=True)
    print("=" * 62, flush=True)
    print("  IMPORTANT : Laissez cette fenêtre ouverte pendant toute la durée.", flush=True)
    print("  Pour couper l'accès et libérer le port 8088, fermez cette fenêtre.", flush=True)
    print("=" * 62, flush=True)
    print("", flush=True)

    def accept_loop():
        while True:
            try:
                sock, addr = server.accept()
            except OSError:
                break
            try:
                chan = transport.open_channel(
                    "direct-tcpip",
                    (REMOTE_HOST, REMOTE_PORT),
                    addr,
                )
            except Exception as exc:
                print("erreur canal:", exc, flush=True)
                sock.close()
                continue
            threading.Thread(target=forward, args=(chan, sock), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()

    # Keepalive heartbeat
    try:
        while True:
            if not transport.is_active():
                print("Tunnel SSH coupé.", flush=True)
                return 1
            time.sleep(5)
    except KeyboardInterrupt:
        print("Tunnel fermé.", flush=True)
        return 0
    finally:
        try:
            server.close()
        except Exception:
            pass
        client.close()


if __name__ == "__main__":
    sys.exit(main())
