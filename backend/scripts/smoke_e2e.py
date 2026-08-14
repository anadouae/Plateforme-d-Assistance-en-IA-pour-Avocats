#!/usr/bin/env python3
"""Smoke E2E Sanad — auth, case, PDF, synthèse, export, analyse, join, polish.

Usage (host, API sur :8001) :
  python backend/scripts/smoke_e2e.py

Ou dans le container :
  docker compose exec backend python scripts/smoke_e2e.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

API = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001").rstrip("/")
EMAIL = "demo@sanad.ma"
PASSWORD = "Sanad2026!"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PDF = FIXTURES / "sanad-test-document.pdf"
WAV = FIXTURES / "sanad-test-audio.wav"


def ok(label: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def main() -> None:
    with httpx.Client(base_url=API, timeout=180.0) as c:
        r = c.get("/api/health/live")
        ok("/api/health/live", r.status_code == 200, str(r.status_code))

        r = c.get("/health/live")
        ok("/health/live", r.status_code == 200)

        r = c.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        ok("login", r.status_code == 200, str(r.status_code))
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        r = c.get("/api/auth/me", headers=h)
        ok("/me", r.status_code == 200 and r.json().get("email") == EMAIL)

        r = c.post(
            "/api/cases",
            headers=h,
            json={
                "client_name": "Smoke E2E Client",
                "case_type": "civil",
                "priority": "normal",
            },
        )
        ok("create case", r.status_code == 201, str(r.status_code))
        case_id = r.json()["id"]

        assert PDF.is_file(), f"missing {PDF}"
        with PDF.open("rb") as f:
            r = c.post(
                "/api/documents/upload",
                headers=h,
                data={"case_id": case_id},
                files={"file": ("sanad-test-document.pdf", f, "application/pdf")},
            )
        ok("upload PDF", r.status_code == 201, str(r.status_code))
        doc_id = r.json()["id"]

        indexed = False
        preview_len = 0
        for i in range(36):
            r = c.get(f"/api/documents/{doc_id}", headers=h)
            d = r.json()
            preview_len = len(d.get("extracted_text_preview") or "")
            st = d.get("status")
            print(f"  … doc poll {i+1}: status={st} preview={preview_len}")
            if st == "indexed" and preview_len > 40:
                indexed = True
                break
            if st == "failed":
                break
            time.sleep(5)
        ok("PDF extracted+indexed", indexed, f"preview={preview_len}")

        t0 = time.time()
        r = c.get(f"/api/documents/{doc_id}/synthese?lang=fr", headers=h)
        ok("synthesis", r.status_code == 200 and len(r.json().get("summary") or "") > 80)
        print(f"  … synthesis in {time.time()-t0:.1f}s")

        r = c.post(
            f"/api/documents/{doc_id}/ask",
            headers=h,
            json={"question": "Quel est le montant ?", "language": "fr"},
        )
        ok("ask document", r.status_code == 200 and "25000" in (r.json().get("answer") or "").replace(" ", ""))

        r = c.post(f"/api/cases/{case_id}/analyse?lang=fr", headers=h)
        ok("case analyse", r.status_code == 200, str(r.status_code))

        r = c.post(
            "/api/plaidoirie-templates/export-docx",
            headers=h,
            json={
                "title": "Smoke plaidoirie",
                "body": "السيد الرئيس،\n\nهذا اختبار تصدير Word.",
            },
        )
        ok(
            "export docx",
            r.status_code == 200
            and "application/" in (r.headers.get("content-type") or "")
            and len(r.content) > 1000,
            f"bytes={len(r.content)}",
        )

        r = c.post(
            "/api/dictation/polish",
            headers=h,
            json={"text": "السيد الرئيس انا ادافع عن زبني", "language": "ar"},
        )
        ok("polish", r.status_code == 200 and bool(r.json().get("polished")))

        r = c.get("/api/team/join-code", headers=h)
        ok("join-code", r.status_code == 200 and bool(r.json().get("join_code")))

        # Assistant RBAC
        r = c.post(
            "/api/auth/login",
            json={"email": "assistant@sanad.ma", "password": PASSWORD},
        )
        if r.status_code == 200:
            ah = {"Authorization": f"Bearer {r.json()['access_token']}"}
            r = c.get(f"/api/documents/{doc_id}/synthese?lang=fr", headers=ah)
            ok("assistant blocked on synthesis", r.status_code == 403)
        else:
            print("[SKIP] assistant login unavailable")

        if WAV.is_file() and WAV.stat().st_size > 50_000:
            with WAV.open("rb") as f:
                r = c.post(
                    "/api/documents/upload",
                    headers=h,
                    data={"case_id": case_id},
                    files={"file": ("sanad-test-audio.wav", f, "audio/wav")},
                )
            ok("upload audio", r.status_code == 201)
            aid = r.json()["id"]
            audio_ok = False
            for i in range(48):
                r = c.get(f"/api/documents/{aid}", headers=h)
                d = r.json()
                st = d.get("status")
                plen = len(d.get("extracted_text_preview") or "")
                print(f"  … audio poll {i+1}: status={st} preview={plen}")
                if st == "indexed" and plen > 5:
                    audio_ok = True
                    break
                if st == "failed":
                    print(f"  … audio error: {d.get('error_message')}")
                    break
                time.sleep(5)
            ok("audio transcribed", audio_ok)
        else:
            print("[SKIP] audio fixture missing/too small")

        print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
