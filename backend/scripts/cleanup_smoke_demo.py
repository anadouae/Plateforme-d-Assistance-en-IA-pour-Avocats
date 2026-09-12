#!/usr/bin/env python3
"""Supprime uniquement les données smoke du Cabinet Démo Atlas (prod-safe)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_

from app.core.database import SessionLocal
from app.models import (
    AgendaEvent,
    Cabinet,
    Case,
    CaseNote,
    CaseTask,
    Document,
    PlaidoirieDraft,
    User,
)
from app.services.rag import delete_document_index
from app.services.storage import delete_file

DEMO_CABINET_NAME = "Cabinet Démo Atlas"
DEMO_EMAIL = "demo@sanad.ma"
SMOKE = "%smoke%"


def _smoke_case_filter():
    return or_(
        Case.client_name.ilike(SMOKE),
        Case.reference.ilike(SMOKE),
        Case.description.ilike(SMOKE),
        Case.tags.ilike(SMOKE),
        Case.case_type.ilike(SMOKE),
    )


def _smoke_doc_filter():
    return or_(
        Document.original_name.ilike(SMOKE),
        Document.filename.ilike(SMOKE),
        Document.original_name.ilike("%smoke-lexhub%"),
        Document.filename.ilike("%smoke-lexhub%"),
    )


def _purge_docs(db, docs: list[Document]) -> int:
    n = 0
    for doc in docs:
        try:
            delete_document_index(doc.cabinet_id, doc.case_id, doc.id)
        except Exception as exc:
            print(f"  warn index: {doc.id}: {exc}")
        try:
            delete_file(doc.storage_path)
        except Exception as exc:
            print(f"  warn storage: {doc.id}: {exc}")
        db.delete(doc)
        n += 1
    return n


def _resolve_demo_cabinet(db) -> Cabinet | None:
    cab = db.query(Cabinet).filter(Cabinet.name == DEMO_CABINET_NAME).first()
    if cab:
        return cab
    user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if user:
        return db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    return None


def cleanup() -> None:
    db = SessionLocal()
    try:
        cab = _resolve_demo_cabinet(db)
        if not cab:
            print(f"Cabinet introuvable ({DEMO_CABINET_NAME} / {DEMO_EMAIL})")
            return

        print(f"Cabinet: {cab.name} ({cab.id})")

        cases = (
            db.query(Case)
            .filter(Case.cabinet_id == cab.id)
            .filter(_smoke_case_filter())
            .all()
        )
        print(f"Smoke cases: {len(cases)}")
        deleted_docs = 0
        deleted_drafts = 0
        deleted_notes = 0
        deleted_tasks = 0
        deleted_events = 0
        refs: list[str] = []

        for case in cases:
            docs = db.query(Document).filter(Document.case_id == case.id).all()
            deleted_docs += _purge_docs(db, docs)
            deleted_notes += (
                db.query(CaseNote)
                .filter(CaseNote.case_id == case.id)
                .delete(synchronize_session=False)
            )
            deleted_tasks += (
                db.query(CaseTask)
                .filter(CaseTask.case_id == case.id)
                .delete(synchronize_session=False)
            )
            deleted_events += (
                db.query(AgendaEvent)
                .filter(AgendaEvent.case_id == case.id)
                .delete(synchronize_session=False)
            )
            deleted_drafts += (
                db.query(PlaidoirieDraft)
                .filter(PlaidoirieDraft.case_id == case.id)
                .delete(synchronize_session=False)
            )
            refs.append(f"{case.reference} | {case.client_name}")
            db.delete(case)

        orphan_docs = (
            db.query(Document)
            .filter(Document.cabinet_id == cab.id)
            .filter(_smoke_doc_filter())
            .all()
        )
        orphan_n = _purge_docs(db, orphan_docs)

        db.commit()

        print("--- deleted ---")
        for r in refs:
            print(f"  case: {r}")
        print(f"cases={len(cases)} docs={deleted_docs + orphan_n} (orphan_docs={orphan_n})")
        print(
            f"notes={deleted_notes} tasks={deleted_tasks} "
            f"agenda={deleted_events} drafts={deleted_drafts}"
        )

        remaining = (
            db.query(Case)
            .filter(Case.cabinet_id == cab.id)
            .filter(_smoke_case_filter())
            .count()
        )
        remaining_docs = (
            db.query(Document)
            .filter(Document.cabinet_id == cab.id)
            .filter(_smoke_doc_filter())
            .count()
        )
        print(f"remaining smoke cases={remaining} smoke docs={remaining_docs}")
        left = (
            db.query(Case.reference, Case.client_name)
            .filter(Case.cabinet_id == cab.id)
            .order_by(Case.reference)
            .all()
        )
        print(f"remaining cases in cabinet ({len(left)}):")
        for ref, client in left:
            print(f"  {ref} | {client}")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n=== Cleanup smoke — Cabinet Démo Atlas ===\n")
    cleanup()
