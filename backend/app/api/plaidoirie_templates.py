"""Templates de plaidoirie personnalisés (cabinet) + export Word .docx."""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_roles
from app.core.database import get_db
from app.models import (
    CabinetPlaidoirieTemplate,
    Case,
    CabinetNotification,
    PlaidoirieDraft,
    PlaidoirieRevision,
    User,
    UserRole,
)
from app.schemas import (
    CabinetPlaidoirieTemplateCreate,
    CabinetPlaidoirieTemplateResponse,
    CabinetPlaidoirieTemplateUpdate,
    PlaidoirieAssignRequest,
    PlaidoirieDocxRequest,
    PlaidoirieDraftCreate,
    PlaidoirieDraftResponse,
    PlaidoirieDraftUpdate,
)
from app.services.docx_export import build_plaidoirie_docx
from app.services.pdf_export import build_plaidoirie_pdf

router = APIRouter(prefix="/api/plaidoirie-templates", tags=["plaidoirie-templates"])


def _draft_to_response(
    db: Session,
    row: PlaidoirieDraft,
    refs: dict[str, str] | None = None,
) -> PlaidoirieDraftResponse:
    import json

    checks: list[str] = []
    if row.checks_json:
        try:
            parsed = json.loads(row.checks_json)
            checks = parsed if isinstance(parsed, list) else []
        except Exception:
            checks = []
    case_ref = None
    if row.case_id:
        if refs is not None:
            case_ref = refs.get(row.case_id)
        else:
            c = (
                db.query(Case)
                .filter(Case.id == row.case_id, Case.cabinet_id == row.cabinet_id)
                .first()
            )
            case_ref = c.reference if c else None
    assignee_name = None
    if getattr(row, "assigned_to_user_id", None):
        u = db.query(User).filter(User.id == row.assigned_to_user_id).first()
        assignee_name = u.full_name if u else None
    citations = []
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
    if st == "finalized":
        badge = "finalisee"
    elif st == "validated":
        badge = "validee"
    else:
        badge = "a_relire"
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
        trust_badge=badge,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_owned(
    db: Session, template_id: str, cabinet_id: str
) -> CabinetPlaidoirieTemplate:
    row = (
        db.query(CabinetPlaidoirieTemplate)
        .filter(
            CabinetPlaidoirieTemplate.id == template_id,
            CabinetPlaidoirieTemplate.cabinet_id == cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Modèle introuvable")
    return row


@router.get("", response_model=list[CabinetPlaidoirieTemplateResponse])
def list_cabinet_templates(
    user: User = Depends(
        require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)
    ),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CabinetPlaidoirieTemplate)
        .filter(CabinetPlaidoirieTemplate.cabinet_id == user.cabinet_id)
        .order_by(CabinetPlaidoirieTemplate.updated_at.desc())
        .all()
    )
    return rows


@router.post(
    "",
    response_model=CabinetPlaidoirieTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cabinet_template(
    data: CabinetPlaidoirieTemplateCreate,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    row = CabinetPlaidoirieTemplate(
        cabinet_id=user.cabinet_id,
        created_by=user.id,
        name=data.name.strip(),
        body=data.body.strip(),
        base_type=(data.base_type or "libre").strip() or "libre",
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    log_audit(db, "plaidoirie_template.create", user=user, request=request, details=row.name)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{template_id}", response_model=CabinetPlaidoirieTemplateResponse)
def update_cabinet_template(
    template_id: str,
    data: CabinetPlaidoirieTemplateUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    row = _get_owned(db, template_id, user.cabinet_id)
    if data.name is not None:
        row.name = data.name.strip()
    if data.body is not None:
        row.body = data.body.strip()
    if data.base_type is not None:
        row.base_type = data.base_type.strip() or None
    row.updated_at = datetime.now(timezone.utc)
    log_audit(db, "plaidoirie_template.update", user=user, request=request, details=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cabinet_template(
    template_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    row = _get_owned(db, template_id, user.cabinet_id)
    db.delete(row)
    log_audit(db, "plaidoirie_template.delete", user=user, request=request, details=template_id)
    db.commit()
    return None


@router.post("/export-docx")
def export_plaidoirie_docx(
    data: PlaidoirieDocxRequest,
    request: Request,
    user: User = Depends(
        require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)
    ),
    db: Session = Depends(get_db),
):
    from urllib.parse import quote

    from app.core.rate_limit import check_rate_limit
    from app.models import Cabinet
    from app.services.object_storage import read_file

    check_rate_limit(
        request,
        key=f"plaidoirie.export_docx:{user.id}",
        limit=20,
        window_sec=60,
    )
    try:
        cabinet = (
            db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
            if not user.cabinet
            else user.cabinet
        )
        cabinet_name = (cabinet.name if cabinet else None) or data.cabinet_name
        cabinet_name_ar = getattr(cabinet, "name_ar", None) if cabinet else None
        if not cabinet_name_ar and data.cabinet_name and cabinet_name != data.cabinet_name:
            # client a envoyé un nom AR distinct
            cabinet_name_ar = data.cabinet_name
        lawyer_name = data.lawyer_name or (
            getattr(user, "full_name_ar", None) or user.full_name
        )
        city = data.city or (getattr(cabinet, "city", None) if cabinet else None)
        logo_bytes = None
        if cabinet and getattr(cabinet, "logo_path", None):
            try:
                logo_bytes = read_file(cabinet.logo_path)
            except Exception:
                logo_bytes = None
        content, filename = build_plaidoirie_docx(
            title=data.title,
            body=data.body,
            cabinet_name=cabinet_name,
            cabinet_name_ar=cabinet_name_ar,
            lawyer_name=lawyer_name,
            city=city,
            case_reference=data.case_reference,
            client_name=data.client_name,
            cabinet_logo_bytes=logo_bytes,
            include_esignature=bool(getattr(data, "include_esignature", False)),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Export Word impossible: {exc}",
        ) from exc

    log_audit(db, "plaidoirie.export_docx", user=user, request=request, details=filename)
    db.commit()
    safe_ascii = "plaidoirie.docx"
    encoded = quote(filename)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'
            ),
        },
    )


@router.post("/export-pdf")
def export_plaidoirie_pdf(
    data: PlaidoirieDocxRequest,
    request: Request,
    user: User = Depends(
        require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)
    ),
    db: Session = Depends(get_db),
):
    from urllib.parse import quote

    from app.core.rate_limit import check_rate_limit
    from app.models import Cabinet

    check_rate_limit(
        request,
        key=f"plaidoirie.export_pdf:{user.id}",
        limit=20,
        window_sec=60,
    )

    try:
        cabinet = (
            db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
            if not user.cabinet
            else user.cabinet
        )
        cabinet_name = (cabinet.name if cabinet else None) or data.cabinet_name
        cabinet_name_ar = getattr(cabinet, "name_ar", None) if cabinet else None
        if not cabinet_name_ar and data.cabinet_name and cabinet_name != data.cabinet_name:
            cabinet_name_ar = data.cabinet_name
        lawyer_name = data.lawyer_name or (
            getattr(user, "full_name_ar", None) or user.full_name
        )
        city = data.city or (getattr(cabinet, "city", None) if cabinet else None)
        logo_bytes = None
        if cabinet and getattr(cabinet, "logo_path", None):
            try:
                from app.services.object_storage import read_file

                logo_bytes = read_file(cabinet.logo_path)
            except Exception:
                logo_bytes = None
        content, filename = build_plaidoirie_pdf(
            title=data.title,
            body=data.body,
            cabinet_name=cabinet_name,
            cabinet_name_ar=cabinet_name_ar,
            lawyer_name=lawyer_name,
            city=city,
            case_reference=data.case_reference,
            client_name=data.client_name,
            cabinet_logo_bytes=logo_bytes,
            include_esignature=bool(getattr(data, "include_esignature", False)),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Export PDF impossible: {exc}",
        ) from exc

    log_audit(db, "plaidoirie.export_pdf", user=user, request=request, details=filename)
    db.commit()
    safe_ascii = "plaidoirie.pdf"
    encoded = quote(filename)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'
            ),
        },
    )


@router.get("/drafts", response_model=list[PlaidoirieDraftResponse])
def list_plaidoirie_drafts(
    user: User = Depends(
        require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)
    ),
    db: Session = Depends(get_db),
):
    q = db.query(PlaidoirieDraft).filter(PlaidoirieDraft.cabinet_id == user.cabinet_id)
    if user.role == UserRole.ASSISTANT:
        q = q.filter(PlaidoirieDraft.status.in_(("validated", "finalized")))
    rows = q.order_by(
        PlaidoirieDraft.pinned.desc(),
        PlaidoirieDraft.updated_at.desc(),
    ).limit(80).all()

    case_ids = {r.case_id for r in rows if r.case_id}
    refs: dict[str, str] = {}
    if case_ids:
        for c in db.query(Case).filter(Case.id.in_(case_ids), Case.cabinet_id == user.cabinet_id).all():
            refs[c.id] = c.reference
    return [_draft_to_response(db, r, refs) for r in rows]


@router.get("/drafts/{draft_id}", response_model=PlaidoirieDraftResponse)
def get_plaidoirie_draft(
    draft_id: str,
    user: User = Depends(
        require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)
    ),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")
    if user.role == UserRole.ASSISTANT and (row.status or "draft") not in ("validated", "finalized"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Plaidoirie non validée")
    return _draft_to_response(db, row)


@router.post("/drafts", response_model=PlaidoirieDraftResponse, status_code=status.HTTP_201_CREATED)
def save_plaidoirie_draft(
    data: PlaidoirieDraftCreate,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    import json

    now = datetime.now(timezone.utc)
    st = (data.status or "draft").strip().lower()
    if st not in ("draft", "validated", "finalized"):
        st = "draft"
    from app.services.legal_citations import extract_citations

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


@router.patch("/drafts/{draft_id}", response_model=PlaidoirieDraftResponse)
def update_plaidoirie_draft(
    draft_id: str,
    data: PlaidoirieDraftUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Rattacher / détacher un dossier sur une plaidoirie existante."""
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")

    if data.case_id is not None:
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

    if data.checks is not None:
        import json as _json

        row.checks_json = _json.dumps(data.checks, ensure_ascii=False)

    if data.status is not None:
        st = (data.status or "draft").strip().lower()
        if st not in ("draft", "validated", "finalized"):
            raise HTTPException(status_code=400, detail="Statut invalide")
        row.status = st
        if st == "validated":
            row.validated_by = user.id
            row.validated_at = datetime.now(timezone.utc)
        elif st == "draft":
            row.validated_by = None
            row.validated_at = None

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
    log_audit(
        db,
        "plaidoirie.draft_update",
        user=user,
        request=request,
        details=f"{row.title[:40]}→{row.case_id or 'sans dossier'}",
    )
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)


@router.post("/drafts/{draft_id}/validate", response_model=PlaidoirieDraftResponse)
def validate_plaidoirie_draft(
    draft_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Marque la plaidoirie comme validée → visible par l'assistant."""
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")
    row.status = "validated"
    row.updated_at = datetime.now(timezone.utc)
    # Notifier les assistants du cabinet
    title_fr = f"Nouvelle plaidoirie validée : {row.title[:80]}"
    body_fr = "L’avocat a validé une plaidoirie. Vous pouvez l’ouvrir, l’imprimer ou la télécharger."
    db.add(
        CabinetNotification(
            cabinet_id=user.cabinet_id,
            user_id=None,
            role_target=UserRole.ASSISTANT.value,
            type="plaidoirie.validated",
            title=title_fr,
            body=body_fr,
            href="/redaction",
            payload_json=None,
            created_at=datetime.now(timezone.utc),
        )
    )
    log_audit(db, "plaidoirie.validate", user=user, request=request, details=row.title[:80])
    db.commit()
    try:
        from app.services.realtime import publish_cabinet_event

        publish_cabinet_event(
            user.cabinet_id,
            "plaidoirie.validated",
            {"id": row.id, "title": row.title[:80]},
        )
    except Exception:
        pass

    # Emails en arrière-plan — ne pas bloquer Valider (Resend peut prendre plusieurs secondes)
    cabinet_id = user.cabinet_id
    plea_title = row.title[:120]
    lawyer_name = user.full_name or user.email

    def _notify_assistants_email() -> None:
        from app.core.database import SessionLocal
        from app.models import Cabinet
        from app.services.email import send_plea_validated_email

        s = SessionLocal()
        try:
            cab = s.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
            cab_name = cab.name if cab else "Cabinet"
            assistants = (
                s.query(User)
                .filter(
                    User.cabinet_id == cabinet_id,
                    User.role == UserRole.ASSISTANT,
                    User.is_active.is_(True),
                )
                .all()
            )
            for a in assistants:
                try:
                    send_plea_validated_email(
                        a.email,
                        assistant_name=a.full_name or a.email,
                        lawyer_name=lawyer_name,
                        plea_title=plea_title,
                        cabinet_name=cab_name,
                    )
                except Exception:
                    continue
        finally:
            s.close()

    background_tasks.add_task(_notify_assistants_email)
    db.refresh(row)
    return _draft_to_response(db, row)


@router.post("/drafts/{draft_id}/unvalidate", response_model=PlaidoirieDraftResponse)
def unvalidate_plaidoirie_draft(
    draft_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Repasse en brouillon (retire de la vue assistant)."""
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")
    row.status = "draft"
    row.updated_at = datetime.now(timezone.utc)
    log_audit(db, "plaidoirie.unvalidate", user=user, request=request, details=row.title[:80])
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)


@router.post("/drafts/{draft_id}/assign", response_model=PlaidoirieDraftResponse)
def assign_plaidoirie_draft(
    draft_id: str,
    data: PlaidoirieAssignRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")
    target_id = (data.user_id or "").strip() or None
    if target_id:
        target = (
            db.query(User)
            .filter(
                User.id == target_id,
                User.cabinet_id == user.cabinet_id,
                User.role == UserRole.ASSISTANT,
                User.is_active.is_(True),
            )
            .first()
        )
        if not target:
            raise HTTPException(status_code=400, detail="Assistant introuvable dans ce cabinet")
        row.assigned_to_user_id = target.id
        if (row.status or "draft") not in ("validated", "finalized"):
            row.status = "validated"
        db.add(
            CabinetNotification(
                cabinet_id=user.cabinet_id,
                user_id=target.id,
                role_target=None,
                type="plaidoirie.assigned",
                title=f"Plaidoirie assignée : {row.title[:80]}",
                body=f"{user.full_name} vous a assigné cette plaidoirie.",
                href="/redaction",
                created_at=datetime.now(timezone.utc),
            )
        )
        log_audit(db, "plaidoirie.assign", user=user, request=request, details=f"{row.title[:40]}->{target.email}")
    else:
        row.assigned_to_user_id = None
        log_audit(db, "plaidoirie.unassign", user=user, request=request, details=row.title[:80])
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)


@router.post("/drafts/{draft_id}/pin", response_model=PlaidoirieDraftResponse)
def pin_plaidoirie_draft(
    draft_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET, UserRole.ASSISTANT)),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaidoirie introuvable")
    if user.role == UserRole.ASSISTANT and (row.status or "draft") not in ("validated", "finalized"):
        raise HTTPException(status_code=403, detail="Non autorisé")
    row.pinned = not bool(row.pinned)
    row.updated_at = datetime.now(timezone.utc)
    log_audit(db, "plaidoirie.pin" if row.pinned else "plaidoirie.unpin", user=user, request=request, details=row.title[:80])
    db.commit()
    db.refresh(row)
    return _draft_to_response(db, row)


@router.delete("/drafts/{draft_id}")
def delete_plaidoirie_draft(
    draft_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    row = (
        db.query(PlaidoirieDraft)
        .filter(
            PlaidoirieDraft.id == draft_id,
            PlaidoirieDraft.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brouillon introuvable")
    title = row.title[:80]
    db.delete(row)
    log_audit(db, "plaidoirie.draft_delete", user=user, request=request, details=title)
    db.commit()
    return {"message": "Brouillon supprimé"}


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
    if user.role == UserRole.ASSISTANT and (row.status or "draft") not in ("validated", "finalized"):
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
