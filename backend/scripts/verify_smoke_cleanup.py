#!/usr/bin/env python3
"""Verify no smoke leftovers in Cabinet Démo Atlas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import or_

from app.core.database import SessionLocal
from app.models import Cabinet, Case, Document

db = SessionLocal()
cab = db.query(Cabinet).filter(Cabinet.name == "Cabinet Démo Atlas").first()
print("cabinet", cab.name if cab else None, cab.id if cab else None)
if not cab:
    raise SystemExit(1)

cases = db.query(Case).filter(Case.cabinet_id == cab.id).order_by(Case.reference).all()
print(f"cases={len(cases)}")
for x in cases:
    print(f"  CASE {x.reference} | {x.client_name}")

docs = db.query(Document).filter(Document.cabinet_id == cab.id).all()
print(f"docs={len(docs)}")
for d in docs:
    print(f"  DOC {d.original_name} | {d.filename}")

smoke_cases = (
    db.query(Case)
    .filter(Case.cabinet_id == cab.id)
    .filter(
        or_(
            Case.client_name.ilike("%smoke%"),
            Case.reference.ilike("%smoke%"),
            Case.description.ilike("%smoke%"),
            Case.tags.ilike("%smoke%"),
        )
    )
    .count()
)
smoke_docs = (
    db.query(Document)
    .filter(Document.cabinet_id == cab.id)
    .filter(
        or_(
            Document.original_name.ilike("%smoke%"),
            Document.filename.ilike("%smoke%"),
            Document.original_name.ilike("%lexhub%"),
        )
    )
    .count()
)
print(f"remaining_smoke_cases={smoke_cases} remaining_smoke_docs={smoke_docs}")
db.close()
