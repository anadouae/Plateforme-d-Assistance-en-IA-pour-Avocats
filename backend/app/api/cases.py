from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit
from app.core.database import get_db
from app.models import Case, Document, User, UserRole
from app.schemas import CaseAnalysisResponse, CaseCreate, CaseResponse, CaseUpdate
from app.services.language import get_disclaimer, normalize_locale

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _case_to_response(case: Case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        reference=case.reference,
        client_name=case.client_name,
        case_type=case.case_type,
        status=case.status,
        responsible_name=case.responsible.full_name if case.responsible else "",
        description=case.description,
        tags=case.tags.split(",") if case.tags else [],
        opened_at=case.opened_at,
        updated_at=case.updated_at,
    )


def _generate_reference(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Case).count() + 1
    return f"WV-{year}-{count:04d}"


@router.get("", response_model=list[CaseResponse])
def list_cases(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cases = (
        db.query(Case)
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
    case = Case(
        reference=_generate_reference(db),
        client_name=data.client_name,
        case_type=data.case_type,
        status=data.status,
        description=data.description,
        tags=",".join(data.tags) if data.tags else None,
        cabinet_id=user.cabinet_id,
        responsible_id=user.id,
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas l'autorisation d'accéder à l'analyse IA.",
        )

    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    docs = (
        db.query(Document)
        .filter(Document.case_id == case.id, Document.cabinet_id == user.cabinet_id)
        .all()
    )
    payload = [
        {"name": d.original_name, "text": d.extracted_text or "", "id": d.id}
        for d in docs
    ]

    from app.services.agent import generate_case_analysis

    locale = normalize_locale(lang)
    data = generate_case_analysis(case.reference, user.cabinet_id, case.id, payload, language=locale)
    log_audit(
        db,
        "case.analyse",
        user=user,
        request=request,
        details=f"{case.reference} docs={len(docs)} score={data.get('confidence_score')}",
    )
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
        elif value is not None:
            setattr(case, field, value)

    case.updated_at = datetime.now(timezone.utc)
    log_audit(db, "case.update", user=user, request=request, details=case.reference)
    db.commit()
    db.refresh(case)
    return _case_to_response(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Les assistants ne peuvent pas supprimer un dossier.",
        )

    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == user.cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    log_audit(db, "case.delete", user=user, request=request, details=case.reference)
    db.delete(case)
    db.commit()
