"""Persistance mapping PII par dossier (cabinet-scoped)."""
from __future__ import annotations
import json
from sqlalchemy.orm import Session
from app.models import Case
from app.services.pii_mask import merge_mappings

def load_case_pii_mapping(case: Case | None) -> dict[str, str]:
    if not case:
        return {}
    raw = getattr(case, "pii_mapping_json", None) or ""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items() if k and v}
    except Exception:
        return {}
    return {}

def save_case_pii_mapping(db: Session, case: Case, mapping: dict[str, str]) -> None:
    if not case or not mapping:
        return
    prev = load_case_pii_mapping(case)
    merged = merge_mappings(prev, mapping)
    case.pii_mapping_json = json.dumps(merged, ensure_ascii=False)
    db.add(case)

def parties_from_case(case: Case | None) -> list[str]:
    if not case:
        return []
    out = []
    if case.client_name:
        out.append(case.client_name)
    if getattr(case, "opposing_name", None):
        out.append(case.opposing_name)
    return out
