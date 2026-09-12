# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")


def wb(rel, text):
    p = ROOT / rel
    tmp = p.with_suffix(p.suffix + ".wtmp")
    tmp.write_text(text, encoding="utf-8")
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)


# Fix ICS escapes
wp = ROOT / "backend/app/api/workspace.py"
wt = wp.read_text(encoding="utf-8")
wt = wt.replace('.replace(",", "\\,")', '.replace(",", "\\\\,")')
# update_task assignee
if 'if "assignee_id" in data.model_dump' not in wt:
    wt = wt.replace(
        "    if data.due_at is not None:\n        task.due_at = data.due_at\n    db.commit()\n    db.refresh(task)\n    return _task_resp(db, task)",
        "    if data.due_at is not None:\n        task.due_at = data.due_at\n"
        "    if \"assignee_id\" in data.model_dump(exclude_unset=True):\n"
        "        task.assignee_id = data.assignee_id\n"
        "    task.updated_at = datetime.now(timezone.utc)\n"
        "    db.commit()\n    db.refresh(task)\n    return _task_resp(db, task)",
        1,
    )
wb("backend/app/api/workspace.py", wt)
print("workspace fixes")

# Email reminder_label
ep = ROOT / "backend/app/services/email.py"
et = ep.read_text(encoding="utf-8")
if "reminder_label: str | None = None" not in et:
    et = et.replace(
        """def send_agenda_reminder_email(
    to: str,
    *,
    full_name: str,
    event_title: str,
    starts_at_label: str,
    event_type_label: str,
    cabinet_name: str,
    case_reference: str | None = None,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/agenda"
    subject = f"{_BRAND} — Rappel agenda sous 48 h ({cabinet_name})"
""",
        """def send_agenda_reminder_email(
    to: str,
    *,
    full_name: str,
    event_title: str,
    starts_at_label: str,
    event_type_label: str,
    cabinet_name: str,
    case_reference: str | None = None,
    reminder_label: str | None = None,
) -> bool:
    url = f"{settings.FRONTEND_URL.rstrip('/')}/agenda"
    when_tag = reminder_label or "J-2"
    subject = f"{_BRAND} — Rappel agenda {when_tag} ({cabinet_name})"
""",
    )
    et = et.replace(
        '        "Rappel agenda — sous 48 heures",',
        '        f"Rappel agenda — {when_tag}",',
        1,
    )
    wb("backend/app/services/email.py", et)
    print("email OK")
else:
    print("email already")

# Plaidoirie draft response + revisions
pp = ROOT / "backend/app/api/plaidoirie_templates.py"
pt = pp.read_text(encoding="utf-8")
if "trust_badge" not in pt:
    pt = pt.replace(
        "from app.models import CabinetPlaidoirieTemplate, Case, CabinetNotification, PlaidoirieDraft, User, UserRole",
        "from app.models import (\n"
        "    CabinetPlaidoirieTemplate,\n"
        "    Case,\n"
        "    CabinetNotification,\n"
        "    PlaidoirieDraft,\n"
        "    PlaidoirieRevision,\n"
        "    User,\n"
        "    UserRole,\n"
        ")",
        1,
    )
    old_resp_end = """    return PlaidoirieDraftResponse(
        id=row.id,
        title=row.title,
        body=row.body,
        template_id=row.template_id,
        case_id=row.case_id,
        case_reference=case_ref,
        checks=checks,
        status=getattr(row, "status", None) or "draft",
        assigned_to_user_id=getattr(row, "assigned_to_user_id", None),
        assigned_to_name=assignee_name,
        pinned=bool(getattr(row, "pinned", False)),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
"""
    new_resp_end = """    citations = []
    sources = []
    if getattr(row, "citations_json", None):
        try:
            parsed = json.loads(row.citations_json)
            citations = parsed if isinstance(parsed, list) else []
        except Exception:
            citations = []
    if getattr(row, "sources_json", None):
        try:
            parsed = json.loads(row.sources_json)
            sources = parsed if isinstance(parsed, list) else []
        except Exception:
            sources = []
    st = getattr(row, "status", None) or "draft"
    return PlaidoirieDraftResponse(
        id=row.id,
        title=row.title,
        body=row.body,
        template_id=row.template_id,
        case_id=row.case_id,
        case_reference=case_ref,
        checks=checks,
        status=st,
        assigned_to_user_id=getattr(row, "assigned_to_user_id", None),
        assigned_to_name=assignee_name,
        pinned=bool(getattr(row, "pinned", False)),
        output_mode=getattr(row, "output_mode", None),
        citations=citations,
        sources=sources,
        validated_by=getattr(row, "validated_by", None),
        validated_at=getattr(row, "validated_at", None),
        trust_badge="validee" if st == "validated" else "a_relire",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
"""
    if old_resp_end not in pt:
        print("MISS draft response")
    else:
        pt = pt.replace(old_resp_end, new_resp_end, 1)

    # save draft: citations + revision
    old_save = """    row = PlaidoirieDraft(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        case_id=data.case_id or None,
        title=data.title.strip(),
        body=data.body.strip(),
        template_id=data.template_id,
        checks_json=json.dumps(data.checks or [], ensure_ascii=False),
        status=st,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    log_audit(db, "plaidoirie.draft_save", user=user, request=request, details=f"{st}:{row.title[:60]}")
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)
"""
    new_save = """    from app.services.legal_citations import extract_citations

    body = data.body.strip()
    citations = extract_citations(body)
    sources = list(getattr(data, "sources", None) or [])
    if not sources:
        sources = [{"kind": "dictation_or_manual", "label": "Saisie / dictée"}]
    row = PlaidoirieDraft(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        case_id=data.case_id or None,
        title=data.title.strip(),
        body=body,
        template_id=data.template_id,
        checks_json=json.dumps(data.checks or [], ensure_ascii=False),
        status=st,
        output_mode=getattr(data, "output_mode", None) or "ecrite",
        citations_json=json.dumps(citations, ensure_ascii=False),
        sources_json=json.dumps(sources, ensure_ascii=False),
        created_at=now,
        updated_at=now,
    )
    if st == "validated":
        row.validated_by = user.id
        row.validated_at = now
    db.add(row)
    db.flush()
    db.add(
        PlaidoirieRevision(
            draft_id=row.id,
            cabinet_id=user.cabinet_id,
            user_id=user.id,
            body_snapshot=body,
            note="création",
        )
    )
    log_audit(db, "plaidoirie.draft_save", user=user, request=request, details=f"{st}:{row.title[:60]}")
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)
"""
    if old_save not in pt:
        print("MISS save block")
    else:
        pt = pt.replace(old_save, new_save, 1)

    # validate: set validated_by + revision
    old_val = """    row.status = "validated"
"""
    # only first occurrence in validate function - careful
    if "row.validated_by = user.id" not in pt:
        pt = pt.replace(
            """    row.status = "validated"
    row.updated_at = datetime.now(timezone.utc)
""",
            """    row.status = "validated"
    row.validated_by = user.id
    row.validated_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    db.add(
        PlaidoirieRevision(
            draft_id=row.id,
            cabinet_id=user.cabinet_id,
            user_id=user.id,
            body_snapshot=row.body or "",
            note="validation avocat",
        )
    )
""",
            1,
        )

    # update draft body/title
    old_upd = """    if data.case_id is not None:
        cid = (data.case_id or "").strip()
        if not cid:
            row.case_id = None
        else:
            case = (
                db.query(Case)
                .filter(Case.id == cid, Case.cabinet_id == user.cabinet_id)
                .first()
            )
            if not case:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")
            row.case_id = case.id

    row.updated_at = datetime.now(timezone.utc)
"""
    new_upd = """    if data.case_id is not None:
        cid = (data.case_id or "").strip()
        if not cid:
            row.case_id = None
        else:
            case = (
                db.query(Case)
                .filter(Case.id == cid, Case.cabinet_id == user.cabinet_id)
                .first()
            )
            if not case:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")
            row.case_id = case.id

    body_changed = False
    if data.title is not None:
        row.title = data.title.strip()
    if data.body is not None:
        import json as _json
        from app.services.legal_citations import extract_citations

        row.body = data.body.strip()
        row.citations_json = _json.dumps(extract_citations(row.body), ensure_ascii=False)
        body_changed = True
    if data.output_mode is not None:
        row.output_mode = data.output_mode
    if data.sources is not None:
        import json as _json

        row.sources_json = _json.dumps(data.sources, ensure_ascii=False)

    if body_changed:
        db.add(
            PlaidoirieRevision(
                draft_id=row.id,
                cabinet_id=user.cabinet_id,
                user_id=user.id,
                body_snapshot=row.body or "",
                note="révision",
            )
        )

    row.updated_at = datetime.now(timezone.utc)
"""
    if old_upd not in pt:
        print("MISS update block")
    else:
        pt = pt.replace(old_upd, new_upd, 1)

    # revisions list endpoint at end
    if "list_plaidoirie_revisions" not in pt:
        pt = pt.rstrip() + '''


@router.get("/drafts/{draft_id}/revisions")
def list_plaidoirie_revisions(
    draft_id: str,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlaidoirieDraft)
        .filter(PlaidoirieDraft.id == draft_id, PlaidoirieDraft.cabinet_id == user.cabinet_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Plaidoirie introuvable")
    if user.role == UserRole.ASSISTANT and (row.status or "draft") != "validated":
        raise HTTPException(status_code=403, detail="Brouillon non visible")
    revs = (
        db.query(PlaidoirieRevision)
        .filter(PlaidoirieRevision.draft_id == draft_id)
        .order_by(PlaidoirieRevision.created_at.desc())
        .limit(50)
        .all()
    )
    out = []
    for r in revs:
        u = db.query(User).filter(User.id == r.user_id).first()
        out.append(
            {
                "id": r.id,
                "note": r.note,
                "author_name": u.full_name if u else "",
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "body_preview": (r.body_snapshot or "")[:240],
            }
        )
    return out
'''
    wb("backend/app/api/plaidoirie_templates.py", pt)
    print("plaidoirie OK")
else:
    print("plaidoirie already")

# .env.example payment vars
for envrel in ("backend/.env.example", ".env.example"):
    ep = ROOT / envrel
    if not ep.exists():
        continue
    et = ep.read_text(encoding="utf-8")
    if "LEXHUB_BANK_RIB" not in et:
        et = et.rstrip() + """

# Paiement Maroc (virement ICE + prépa CMI/PayZone)
LEXHUB_BANK_RIB=
LEXHUB_BANK_NAME=Attijariwafa Bank
LEXHUB_BANK_BENEFICIARY=WEBVOICE SARL
LEXHUB_COMPANY_ICE=
CMI_ENABLED=false
CMI_MERCHANT_ID=
CMI_STORE_KEY=
CMI_GATEWAY_URL=
PAYZONE_ENABLED=false
PAYZONE_MERCHANT_ID=
PAYZONE_API_KEY=
"""
        wb(envrel, et)
        print("env", envrel)

print("done fixes")
