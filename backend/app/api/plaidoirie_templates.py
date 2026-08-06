"""Templates de plaidoirie personnalisés (cabinet) + export Word .docx."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_roles
from app.core.database import get_db
from app.models import CabinetPlaidoirieTemplate, User, UserRole
from app.schemas import (
    CabinetPlaidoirieTemplateCreate,
    CabinetPlaidoirieTemplateResponse,
    CabinetPlaidoirieTemplateUpdate,
    PlaidoirieDocxRequest,
)
from app.services.docx_export import build_plaidoirie_docx

router = APIRouter(prefix="/api/plaidoirie-templates", tags=["plaidoirie-templates"])


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

    try:
        cabinet_name = data.cabinet_name or (
            user.cabinet.name if user.cabinet else None
        )
        lawyer_name = data.lawyer_name or user.full_name
        city = data.city or (getattr(user.cabinet, "city", None) if user.cabinet else None)
        content, filename = build_plaidoirie_docx(
            title=data.title,
            body=data.body,
            cabinet_name=cabinet_name,
            lawyer_name=lawyer_name,
            city=city,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Export Word impossible: {exc}",
        ) from exc

    log_audit(db, "plaidoirie.export_docx", user=user, request=request, details=filename)
    db.commit()
    # ASCII fallback + UTF-8 filename* (évite échec navigateur sur titres arabes)
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
