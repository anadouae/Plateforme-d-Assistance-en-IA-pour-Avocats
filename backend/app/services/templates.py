"""Legal document template generation (style Adala)."""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def list_templates() -> list[dict]:
    path = DATA_DIR / "document_templates.json"
    if not path.exists():
        return []
    templates = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "category": t["category"],
            "description": t["description"],
            "fields": t["fields"],
        }
        for t in templates
    ]


def get_template(template_id: str) -> dict | None:
    path = DATA_DIR / "document_templates.json"
    if not path.exists():
        return None
    for t in json.loads(path.read_text(encoding="utf-8")):
        if t["id"] == template_id:
            return t
    return None


def generate_document(template_id: str, fields: dict[str, str]) -> dict:
    template = get_template(template_id)
    if not template:
        return {"error": "Modèle introuvable"}

    missing = [f for f in template["fields"] if f not in fields or not fields[f].strip()]
    if missing:
        return {"error": f"Champs manquants : {', '.join(missing)}"}

    content = template["template"]
    for key, value in fields.items():
        content = content.replace(f"{{{{{key}}}}}", value)

    remaining = re.findall(r"\{\{(\w+)\}\}", content)
    if remaining:
        return {"error": f"Variables non remplies : {', '.join(remaining)}"}

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "category": template["category"],
        "content": content,
        "disclaimer": "Ceci ne constitue pas un avis juridique. Faites valider par un avocat.",
    }
