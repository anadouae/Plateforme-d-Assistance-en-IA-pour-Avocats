#!/usr/bin/env python3
"""Supprime les dossiers/documents de démo (WV-2026-*) de la base réelle."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models import AgendaEvent, Case, CaseNote, CaseTask, Document

DEMO_REFERENCES = ("WV-2026-0001", "WV-2026-0002")


def cleanup():
    db = SessionLocal()
    try:
        cases = db.query(Case).filter(Case.reference.in_(DEMO_REFERENCES)).all()
        if not cases:
            print("Aucun dossier démo WV-2026-* trouvé.")
            return

        for case in cases:
            doc_ids = [d.id for d in db.query(Document).filter(Document.case_id == case.id).all()]
            db.query(CaseNote).filter(CaseNote.case_id == case.id).delete()
            db.query(CaseTask).filter(CaseTask.case_id == case.id).delete()
            db.query(AgendaEvent).filter(AgendaEvent.case_id == case.id).delete()
            db.query(Document).filter(Document.case_id == case.id).delete()
            db.delete(case)
            print(f"  Supprimé dossier {case.reference} ({len(doc_ids)} document(s))")

        db.commit()
        print("Nettoyage terminé — seules vos vraies données restent.")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n=== Suppression des données démo ===\n")
    cleanup()
