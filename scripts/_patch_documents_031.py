# -*- coding: utf-8 -*-
"""Patch documents.py for bordereau + meta."""
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")
p = ROOT / "backend/app/api/documents.py"
docs = p.read_text(encoding="utf-8")

if "update_document_meta" in docs:
    print("already")
else:
    if "from fastapi.responses import Response" not in docs:
        docs = docs.replace(
            "from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status\n",
            "from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status\n"
            "from fastapi.responses import Response\n",
            1,
        )
    if "DocumentMetaUpdate" not in docs:
        docs = docs.replace(
            "    DocumentDetailResponse,\n    DocumentResponse,\n",
            "    DocumentDetailResponse,\n    DocumentMetaUpdate,\n    DocumentResponse,\n",
            1,
        )
    if "inventory_number=getattr" not in docs:
        docs = docs.replace(
            "        kind=kind,\n        error_message=doc.error_message,\n    )",
            "        kind=kind,\n        error_message=doc.error_message,\n"
            "        inventory_number=getattr(doc, \"inventory_number\", None),\n"
            "        exhibit_type=getattr(doc, \"exhibit_type\", None),\n"
            "        produced_by=getattr(doc, \"produced_by\", None),\n"
            "        exhibit_version=getattr(doc, \"exhibit_version\", None),\n"
            "        cited_in_plea=getattr(doc, \"cited_in_plea\", None),\n"
            "    )",
            1,
        )
    if "doc.inventory_number = int" not in docs:
        docs = docs.replace(
            "        cabinet_id=user.cabinet_id,\n        uploaded_by=user.id,\n    )\n    db.add(doc)",
            "        cabinet_id=user.cabinet_id,\n        uploaded_by=user.id,\n    )\n"
            "    from sqlalchemy import func\n"
            "    max_n = (\n"
            "        db.query(func.max(Document.inventory_number))\n"
            "        .filter(Document.case_id == case_id, Document.cabinet_id == user.cabinet_id)\n"
            "        .scalar()\n"
            "    )\n"
            "    doc.inventory_number = int(max_n or 0) + 1\n"
            "    if getattr(doc, \"exhibit_version\", None) is None:\n"
            "        doc.exhibit_version = \"copie\"\n"
            "    if getattr(doc, \"produced_by\", None) is None:\n"
            "        doc.produced_by = \"client\"\n"
            "    db.add(doc)",
            1,
        )

    nl = chr(10)
    append_lines = [
        "",
        "",
        '@router.patch("/{doc_id}/meta", response_model=DocumentResponse)',
        "def update_document_meta(",
        "    doc_id: str,",
        "    data: DocumentMetaUpdate,",
        "    request: Request,",
        "    user: User = Depends(get_current_user),",
        "    db: Session = Depends(get_db),",
        "):",
        "    doc = _get_document_for_user(db, doc_id, user)",
        "    for field, value in data.model_dump(exclude_unset=True).items():",
        "        setattr(doc, field, value)",
        "    case = db.query(Case).filter(Case.id == doc.case_id).first()",
        '    log_audit(db, "document.meta", user=user, request=request, details=doc.original_name)',
        "    db.commit()",
        "    db.refresh(doc)",
        "    return _doc_response(doc, case)",
        "",
        "",
        '@router.get("/bordereau/{case_id}")',
        "def export_bordereau(",
        "    case_id: str,",
        "    user: User = Depends(get_current_user),",
        "    db: Session = Depends(get_db),",
        "):",
        "    case = (",
        "        db.query(Case)",
        "        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)",
        "        .first()",
        "    )",
        "    if not case:",
        '        raise HTTPException(status_code=404, detail="Dossier introuvable")',
        "    docs_list = (",
        "        db.query(Document)",
        "        .filter(Document.case_id == case_id, Document.cabinet_id == user.cabinet_id)",
        "        .order_by(Document.inventory_number.asc().nullslast(), Document.created_at.asc())",
        "        .all()",
        "    )",
        "    lines = [",
        '        f"BORDEREAU DE PIECES — {case.reference}",',
        '        f"Client : {case.client_name}",',
        '        f"N° RG : {getattr(case, \'court_file_number\', None) or \'—\'}",',
        '        f"Tribunal : {case.tribunal or \'—\'}",',
        '        "",',
        "        f\"{'N°':<4} {'Type':<16} {'Producteur':<12} {'Version':<12} Intitulé / citation\",",
        '        "-" * 88,',
        "    ]",
        "    for d in docs_list:",
        '        n = getattr(d, "inventory_number", None) or "—"',
        '        et = getattr(d, "exhibit_type", None) or "—"',
        '        pb = getattr(d, "produced_by", None) or "—"',
        '        ev = getattr(d, "exhibit_version", None) or "—"',
        '        cite = getattr(d, "cited_in_plea", None) or ""',
        "        title = d.original_name",
        "        if cite:",
        '            title = f"{title} [cité : {cite}]"',
        '        lines.append(f"{str(n):<4} {et:<16} {pb:<12} {ev:<12} {title}")',
        "    lines.append(\"\")",
        '    lines.append("Document généré par LexHub — sans logo sur l\'acte d\'audience.")',
        f'    body = "{nl}".join(lines)',
        '    filename = f"bordereau-{case.reference}.txt"',
        "    return Response(",
        '        content=body.encode("utf-8"),',
        '        media_type="text/plain; charset=utf-8",',
        '        headers={"Content-Disposition": f\'attachment; filename="{filename}"\'},',
        "    )",
        "",
    ]
    # Fix the join line - use proper Python
    for i, line in enumerate(append_lines):
        if line.startswith("    body = "):
            append_lines[i] = '    body = "\\n".join(lines)'

    docs = docs.rstrip() + "\n" + "\n".join(append_lines) + "\n"
    tmp = p.with_suffix(".py.wtmp")
    tmp.write_text(docs, encoding="utf-8")
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
    print("documents patched")
