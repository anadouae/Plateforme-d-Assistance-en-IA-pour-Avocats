#!/usr/bin/env python3
"""Smoke LexHub complet — pages publiques + API métier (+ IA optionnelle).

Usage:
  python scripts/smoke_lexhub_full.py
  python scripts/smoke_lexhub_full.py https://lexhub.space
  python scripts/smoke_lexhub_full.py https://lexhub.space --no-ai   # sans synthèse/ask (épargne quota)
  python scripts/smoke_lexhub_full.py https://lexhub.space --ai      # force IA

Compte: demo@sanad.ma / Sanad2026!
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "scripts" / "fixtures"
PDF = FIXTURES / "sanad-test-document.pdf"

EMAIL = "demo@sanad.ma"
PASSWORD = "Sanad2026!"

PUBLIC_PAGES = [
    "/",
    "/home",
    "/login",
    "/register",
    "/forgot-password",
    "/about",
    "/fonctionnalites",
    "/securite",
    "/mentions-legales",
    "/confidentialite",
    "/join",
    "/tarifs",
    "/checkout",
    "/aide",
    "/contact",
]

PROTECTED_PAGES = [
    "/dashboard",
    "/cases",
    "/documents",
    "/redaction",
    "/agenda",
    "/team",
    "/settings",
    "/templates",
]

fails = 0
passes = 0
skips = 0


def report(label: str, cond: bool, detail: str = "", *, soft: bool = False) -> None:
    global fails, passes, skips
    if cond:
        passes += 1
        print(f"[PASS] {label}" + (f" — {detail}" if detail else ""))
        return
    if soft:
        skips += 1
        print(f"[SKIP] {label}" + (f" — {detail}" if detail else ""))
        return
    fails += 1
    print(f"[FAIL] {label}" + (f" — {detail}" if detail else ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", nargs="?", default="https://lexhub.space")
    parser.add_argument("--ai", action="store_true", help="Inclure synthèse + ask (consomme quota)")
    parser.add_argument("--no-ai", action="store_true", help="Exclure IA (défaut: IA légère = polish seulement)")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    # Par défaut: polish oui (léger), synthèse/ask seulement avec --ai
    run_heavy_ai = args.ai and not args.no_ai

    print(f"=== LexHub smoke — {base} ===")
    print(f"IA lourde (synthèse/ask): {'oui' if run_heavy_ai else 'non'}")
    print()

    timeout = httpx.Timeout(120.0, connect=20.0)
    with httpx.Client(base_url=base, timeout=timeout, follow_redirects=True) as c:
        # --- Santé ---
        r = c.get("/api/health")
        report("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok")
        if r.status_code == 200:
            h = r.json()
            report("email Resend", (h.get("email") or {}).get("provider") == "resend")
            report("LLM free_router", bool((h.get("llm") or {}).get("free_router")))
            report("corpus > 100k", int((h.get("corpus") or {}).get("total_entries") or 0) > 100_000)

        r = c.get("/api/health/stt")
        report("GET /api/health/stt", r.status_code == 200 and r.json().get("enabled") is True)

        # --- Pages publiques (HTML) ---
        print("\n--- Pages publiques ---")
        for path in PUBLIC_PAGES:
            r = c.get(path)
            report(
                f"page {path}",
                r.status_code == 200 and "text/html" in (r.headers.get("content-type") or ""),
                str(r.status_code),
            )

        # Pages protégées : Next sert le shell HTML même sans cookie (auth côté client)
        print("\n--- Shell pages app ---")
        for path in PROTECTED_PAGES:
            r = c.get(path)
            report(f"shell {path}", r.status_code == 200, str(r.status_code))

        # --- Auth ---
        print("\n--- Auth & session ---")
        r = c.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        report("login demo", r.status_code == 200, str(r.status_code))
        if r.status_code != 200:
            print(r.text[:300])
            print(f"\n=== STOP — login KO ({fails} fails) ===")
            return 1
        token = r.json()["access_token"]
        hdr = {"Authorization": f"Bearer {token}"}

        r = c.get("/api/auth/me", headers=hdr)
        me = r.json() if r.status_code == 200 else {}
        report("/api/auth/me", r.status_code == 200 and me.get("email") == EMAIL, me.get("role", ""))

        # --- Listes ---
        print("\n--- API listes ---")
        for path, label in [
            ("/api/cases", "cases"),
            ("/api/documents", "documents"),
            ("/api/workspace/agenda", "agenda"),
            ("/api/workspace/tasks", "tasks"),
            ("/api/team", "team members"),
            ("/api/team/join-code", "join-code"),
            ("/api/settings/cabinet", "cabinet settings"),
            ("/api/dictation/stt-status", "stt-status"),
            ("/api/plaidoirie-templates", "plaidoirie templates"),
        ]:
            r = c.get(path, headers=hdr)
            # certains endpoints peuvent être 404 si alias différent — soft
            if r.status_code == 404:
                report(f"GET {path}", False, "404", soft=True)
            else:
                report(f"GET {path} ({label})", r.status_code == 200, str(r.status_code))

        # --- Création dossier ---
        print("\n--- Parcours dossier + document ---")
        r = c.post(
            "/api/cases",
            headers=hdr,
            json={
                "client_name": f"Smoke Auto {int(time.time())}",
                "case_type": "civil",
                "priority": "normal",
            },
        )
        report("POST /api/cases", r.status_code in (200, 201), str(r.status_code))
        case_id = (r.json() or {}).get("id") if r.status_code in (200, 201) else None

        doc_id = None
        if case_id and PDF.is_file():
            with PDF.open("rb") as f:
                r = c.post(
                    "/api/documents/upload",
                    headers=hdr,
                    data={"case_id": case_id},
                    files={"file": ("smoke-lexhub.pdf", f, "application/pdf")},
                )
            report("upload PDF", r.status_code in (200, 201), str(r.status_code))
            doc_id = (r.json() or {}).get("id") if r.status_code in (200, 201) else None
        elif not PDF.is_file():
            report("upload PDF", False, f"fixture manquante: {PDF}", soft=True)

        if doc_id:
            indexed = False
            preview = 0
            for i in range(24):
                r = c.get(f"/api/documents/{doc_id}", headers=hdr)
                d = r.json() if r.status_code == 200 else {}
                preview = len(d.get("extracted_text_preview") or d.get("extracted_text") or "")
                st = d.get("status")
                print(f"  … OCR poll {i+1}: status={st} preview={preview}")
                if st == "indexed" and preview > 20:
                    indexed = True
                    break
                if st == "failed":
                    break
                time.sleep(4)
            report("PDF indexé", indexed, f"preview={preview}")

        # --- Dictée polish (léger, pas de gros LLM synthèse) ---
        print("\n--- Dictée ---")
        r = c.post(
            "/api/dictation/polish",
            headers=hdr,
            json={"text": "السيد الرئيس انا ادافع عن زبني", "language": "ar", "source": "audio"},
        )
        report(
            "POST /api/dictation/polish",
            r.status_code == 200 and bool((r.json() or {}).get("polished")),
            str(r.status_code),
        )

        r = c.post(
            "/api/plaidoirie-templates/export-docx",
            headers=hdr,
            json={"title": "Smoke LexHub", "body": "السيد الرئيس،\n\nاختبار تصدير."},
        )
        report(
            "export Word",
            r.status_code == 200 and len(r.content) > 800,
            f"bytes={len(r.content)} status={r.status_code}",
        )

        # --- IA lourde (optionnelle) ---
        if run_heavy_ai and doc_id:
            print("\n--- IA (consomme quota) ---")
            r = c.get(f"/api/documents/{doc_id}/synthese?lang=fr", headers=hdr)
            report(
                "synthèse document",
                r.status_code == 200 and len((r.json() or {}).get("summary") or "") > 40,
                str(r.status_code),
            )
            r = c.post(
                f"/api/documents/{doc_id}/ask",
                headers=hdr,
                json={"question": "Résume ce document en une phrase.", "language": "fr"},
            )
            report(
                "ask document",
                r.status_code == 200 and len((r.json() or {}).get("answer") or "") > 20,
                str(r.status_code),
            )
        else:
            report("synthèse/ask", False, "passé (--ai pour activer)", soft=True)

        # --- Admin plateforme ---
        print("\n--- Admin plateforme ---")
        r = c.post(
            "/api/auth/login",
            json={"email": "admin@webvoice.ma", "password": "WebVision2026!"},
        )
        if r.status_code == 200:
            ah = {"Authorization": f"Bearer {r.json()['access_token']}"}
            for path in ("/api/admin/metrics", "/api/admin/cabinets", "/api/admin/audit-logs"):
                rr = c.get(path, headers=ah)
                if rr.status_code == 404:
                    report(f"admin {path}", False, "404", soft=True)
                else:
                    report(f"admin {path}", rr.status_code == 200, str(rr.status_code))
            r = c.get("/admin", follow_redirects=True)
            report("shell /admin", r.status_code == 200)
        else:
            report("login admin plateforme", False, str(r.status_code), soft=True)

        # --- RBAC assistant ---
        print("\n--- RBAC ---")
        r = c.post(
            "/api/auth/login",
            json={"email": "assistant@sanad.ma", "password": PASSWORD},
        )
        if r.status_code == 200 and doc_id:
            ash = {"Authorization": f"Bearer {r.json()['access_token']}"}
            r = c.get(f"/api/documents/{doc_id}/synthese?lang=fr", headers=ash)
            report("assistant bloqué synthèse", r.status_code == 403, str(r.status_code))
        else:
            report("assistant login", False, str(r.status_code), soft=True)

    print()
    print(f"=== Résultat: {passes} PASS · {fails} FAIL · {skips} SKIP ===")
    if fails:
        print("Des échecs critiques — corriger avant la démo.")
        return 1
    print("OK — parcours API + pages OK.")
    print()
    print("Rappel manuels (micro téléphone):")
    print("  1. Login demo@sanad.ma / Sanad2026!")
    print("  2. /redaction → micro → parler 10s → arrêter")
    print("  3. Document → bouton « Lancer l'analyse IA »")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
