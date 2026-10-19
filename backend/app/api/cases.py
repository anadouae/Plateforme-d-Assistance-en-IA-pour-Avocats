import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, log_audit, require_not_assistant
from app.core.database import get_db
from app.models import (
    AgendaEvent,
    Case,
    Document,
    PlaidoirieDraft,
    PlaidoirieRevision,
    User,
    UserRole,
)
from app.schemas import (
    CaseAnalysisResponse,
    CaseCreate,
    CaseResponse,
    CaseUpdate,
)
from app.services.language import get_disclaimer, normalize_locale
from app.services.case_judicial import compute_appeal_deadline, default_appeal_days
from app.services.rag import delete_document_index
from app.services.storage import delete_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _case_to_response(case: Case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        reference=case.reference,
        title=getattr(case, "title", None) or None,
        client_name=case.client_name,
        case_type=case.case_type,
        status=case.status,
        responsible_name=case.responsible.full_name if case.responsible else "",
        responsible_id=getattr(case, "responsible_id", None),
        description=case.description,
        tags=case.tags.split(",") if case.tags else [],
        opened_at=case.opened_at,
        updated_at=case.updated_at,
        jurisdiction_degree=getattr(case, "jurisdiction_degree", None),
        tribunal=getattr(case, "tribunal", None),
        court_city=getattr(case, "court_city", None),
        client_role=getattr(case, "client_role", None),
        client_quality=getattr(case, "client_quality", None),
        client_domicile=getattr(case, "client_domicile", None),
        opposing_name=getattr(case, "opposing_name", None),
        opposing_role=getattr(case, "opposing_role", None),
        opposing_quality=getattr(case, "opposing_quality", None),
        opposing_domicile=getattr(case, "opposing_domicile", None),
        court_file_number=getattr(case, "court_file_number", None),
        judge_name=getattr(case, "judge_name", None),
        chamber=getattr(case, "chamber", None),
        greffe=getattr(case, "greffe", None),
        procedure_status=getattr(case, "procedure_status", None),
        assistant_id=getattr(case, "assistant_id", None),
        last_decision_type=getattr(case, "last_decision_type", None),
        last_decision_date=getattr(case, "last_decision_date", None),
        notification_date=getattr(case, "notification_date", None),
        appeal_deadline_at=getattr(case, "appeal_deadline_at", None),
        appeal_deadline_days=getattr(case, "appeal_deadline_days", None),
    )


def _generate_reference(db: Session) -> str:
    """Référence unique WV-AAAA-NNNN (évite les collisions après suppressions)."""
    year = datetime.now(timezone.utc).year
    prefix = f"WV-{year}-"
    refs = [r[0] for r in db.query(Case.reference).filter(Case.reference.like(f"{prefix}%")).all()]
    max_n = 0
    for ref in refs:
        try:
            max_n = max(max_n, int(str(ref).rsplit("-", 1)[-1]))
        except ValueError:
            continue
    for _ in range(20):
        max_n += 1
        candidate = f"{prefix}{max_n:04d}"
        exists = db.query(Case.id).filter(Case.reference == candidate).first()
        if not exists:
            return candidate
    # Dernier recours : horodatage
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"{prefix}{stamp}"


@router.get("", response_model=list[CaseResponse])
def list_cases(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cases = (
        db.query(Case)
        .options(joinedload(Case.responsible))
        .filter(Case.cabinet_id == user.cabinet_id)
        .order_by(Case.updated_at.desc())
        .all()
    )
    return [_case_to_response(c) for c in cases]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    data: CaseCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    responsible_id = user.id
    if data.responsible_id:
        assignee = (
            db.query(User)
            .filter(
                User.id == data.responsible_id,
                User.cabinet_id == user.cabinet_id,
                User.is_active.is_(True),
                User.role.in_([UserRole.AVOCAT, UserRole.ADMIN_CABINET]),
            )
            .first()
        )
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Responsable invalide pour ce cabinet",
            )
        responsible_id = assignee.id

    tags = list(data.tags or [])
    description = data.description
    if data.first_hearing_at:
        hearing = data.first_hearing_at.strip()
        if hearing:
            tags.append(f"audience:{hearing}")
            note = f"Première audience : {hearing}"
            description = f"{description}\n{note}".strip() if description else note

    from app.services.billing import assert_can_create_case

    assert_can_create_case(db, user.cabinet_id)

    title = (data.title or "").strip() or None
    if not title:
        # Fallback marché : intitulé = client (+ adverse si connu)
        opp = (data.opposing_name or "").strip()
        title = f"{data.client_name.strip()} c/ {opp}" if opp else data.client_name.strip()

    case = Case(
        reference=_generate_reference(db),
        title=title[:255],
        client_name=data.client_name,
        case_type=data.case_type,
        status=data.status,
        description=description,
        tags=",".join(tags) if tags else None,
        cabinet_id=user.cabinet_id,
        responsible_id=responsible_id,
        jurisdiction_degree=data.jurisdiction_degree,
        tribunal=data.tribunal,
        court_city=getattr(data, "court_city", None),
        client_role=data.client_role,
        client_quality=data.client_quality,
        client_domicile=data.client_domicile,
        opposing_name=data.opposing_name,
        opposing_role=data.opposing_role,
        opposing_quality=data.opposing_quality,
        opposing_domicile=data.opposing_domicile,
        court_file_number=getattr(data, "court_file_number", None),
        judge_name=getattr(data, "judge_name", None),
        chamber=getattr(data, "chamber", None),
        greffe=getattr(data, "greffe", None),
        procedure_status=getattr(data, "procedure_status", None) or "ouverture",
        assistant_id=getattr(data, "assistant_id", None),
        last_decision_type=getattr(data, "last_decision_type", None),
        last_decision_date=getattr(data, "last_decision_date", None),
        notification_date=getattr(data, "notification_date", None),
        appeal_deadline_days=getattr(data, "appeal_deadline_days", None),
        appeal_deadline_at=compute_appeal_deadline(
            getattr(data, "notification_date", None),
            getattr(data, "appeal_deadline_days", None),
            getattr(data, "jurisdiction_degree", None),
        ),
    )
    db.add(case)
    log_audit(db, "case.create", user=user, request=request, details=case.reference)
    db.commit()
    db.refresh(case)
    return _case_to_response(case)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .options(joinedload(Case.responsible))
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")
    return _case_to_response(case)


@router.post("/{case_id}/analyse", response_model=CaseAnalysisResponse)
def analyse_case(
    case_id: str,
    request: Request,
    lang: str | None = None,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    from app.services.billing import begin_ai_action, finish_ai_action
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="cases.analyse", limit=8, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "analyse", request=request)

    docs = (
        db.query(Document)
        .filter(Document.case_id == case.id, Document.cabinet_id == user.cabinet_id)
        .all()
    )
    payload = [
        {"name": d.original_name, "text": d.extracted_text or "", "id": d.id}
        for d in docs
    ]
    # Enrichissement fiche dossier (parties connues même si regex rate)
    meta_bits = []
    if case.client_name:
        meta_bits.append(f"Client / PARTIE_A : {case.client_name}")
    if getattr(case, "opposing_name", None):
        meta_bits.append(f"Adverse / PARTIE_B : {case.opposing_name}")
    if getattr(case, "title", None):
        meta_bits.append(f"Titre : {case.title}")
    if getattr(case, "court_file_number", None):
        meta_bits.append(f"N° greffe : {case.court_file_number}")
    if meta_bits:
        payload.insert(
            0,
            {"name": "_fiche_dossier", "text": "\n".join(meta_bits), "id": "meta"},
        )

    from app.services.agent import generate_case_analysis

    locale = normalize_locale(lang)
    try:
        data = generate_case_analysis(case.reference, user.cabinet_id, case.id, payload, language=locale)
    except Exception:
        finish_ai_action(db, user.cabinet_id, "analyse", slot_token=slot, success=False)
        raise
    log_audit(
        db,
        "case.analyse",
        user=user,
        request=request,
        details=f"{case.reference} docs={len(docs)} score={data.get('confidence_score')}",
    )
    finish_ai_action(db, user.cabinet_id, "analyse", slot_token=slot, success=True)
    db.commit()

    return CaseAnalysisResponse(
        case_id=case.id,
        case_reference=data["case_reference"],
        facts=data["facts"],
        key_documents=data["key_documents"],
        legal_issues=data["legal_issues"],
        risks_and_deadlines=data["risks_and_deadlines"],
        checklist=data["checklist"],
        summary=data["summary"],
        parties=data.get("parties", []),
        key_dates=data.get("key_dates", []),
        amounts=data.get("amounts", []),
        sources=data.get("sources", []),
        confidence_score=data.get("confidence_score", 0),
        disclaimer=data.get("disclaimer", get_disclaimer(locale)),
    )


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    data: CaseUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "tags" and value is not None:
            setattr(case, field, ",".join(value))
        elif field == "title":
            setattr(case, field, (str(value).strip() if value is not None else "") or None)
        elif value is not None:
            setattr(case, field, value)

    # Recalcule délai de recours si notification / jours changés
    payload = data.model_dump(exclude_unset=True)
    if "notification_date" in payload or "appeal_deadline_days" in payload or "jurisdiction_degree" in payload:
        days = case.appeal_deadline_days or default_appeal_days(case.jurisdiction_degree)
        case.appeal_deadline_days = days
        case.appeal_deadline_at = compute_appeal_deadline(
            case.notification_date, days, case.jurisdiction_degree
        )

    case.updated_at = datetime.now(timezone.utc)
    log_audit(db, "case.update", user=user, request=request, details=case.reference)
    db.commit()
    db.refresh(case)
    return _case_to_response(case)


def _purge_case_dependencies(db: Session, case: Case) -> None:
    """Remove/null FK children so deleting a case never hits IntegrityError."""
    docs = db.query(Document).filter(Document.case_id == case.id).all()
    for doc in docs:
        try:
            delete_document_index(doc.cabinet_id, doc.case_id, doc.id)
        except Exception:
            logger.warning("Index delete skipped for %s", doc.id)
        try:
            delete_file(doc.storage_path)
        except Exception:
            logger.warning("Storage delete skipped for %s", doc.id)
        db.delete(doc)

    db.query(AgendaEvent).filter(AgendaEvent.case_id == case.id).delete(synchronize_session=False)

    # Révisions AVANT brouillons (FK draft_id) — sinon IntegrityError et le dossier « revient »
    draft_ids = [
        r[0]
        for r in db.query(PlaidoirieDraft.id).filter(PlaidoirieDraft.case_id == case.id).all()
    ]
    if draft_ids:
        db.query(PlaidoirieRevision).filter(PlaidoirieRevision.draft_id.in_(draft_ids)).delete(
            synchronize_session=False
        )
    db.query(PlaidoirieDraft).filter(PlaidoirieDraft.case_id == case.id).delete(
        synchronize_session=False
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: str,
    request: Request,
    user: User = Depends(require_not_assistant),
    db: Session = Depends(get_db),
):
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    # Admin cabinet : peut supprimer tout dossier du cabinet.
    # Avocat : uniquement s’il est le responsable.
    if user.role != UserRole.ADMIN_CABINET:
        if not case.responsible_id or case.responsible_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul l’avocat responsable (ou l’admin cabinet) peut supprimer ce dossier.",
            )

    log_audit(db, "case.delete", user=user, request=request, details=case.reference)
    _purge_case_dependencies(db, case)
    db.delete(case)
    db.commit()

