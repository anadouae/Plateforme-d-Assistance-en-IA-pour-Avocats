from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_roles
from app.core.database import get_db
from app.models import AuditLog, Cabinet, CabinetStatus, Case, Document, User, UserRole
from app.schemas import AdminCabinetResponse, AdminMetricsResponse, AuditLogResponse, CabinetStatusUpdate, MessageResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/cabinets", response_model=list[AdminCabinetResponse])
def list_cabinets(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    cabinets = (
        db.query(Cabinet)
        .filter(Cabinet.name != "WebVoice Platform")
        .order_by(Cabinet.created_at.desc())
        .all()
    )
    result = []
    for cab in cabinets:
        result.append(
            AdminCabinetResponse(
                id=cab.id,
                name=cab.name,
                city=cab.city,
                barreau=cab.barreau,
                status=cab.status.value,
                user_count=db.query(User).filter(User.cabinet_id == cab.id).count(),
                document_count=db.query(Document).filter(Document.cabinet_id == cab.id).count(),
                case_count=db.query(Case).filter(Case.cabinet_id == cab.id).count(),
                summarize_count=db.query(AuditLog)
                .filter(
                    AuditLog.cabinet_id == cab.id,
                    AuditLog.action.in_(
                        (
                            "document.summarize",
                            "document.summarize_degraded",
                            "case.analyse",
                            "document.synthesize",
                        )
                    ),
                )
                .count(),
                created_at=cab.created_at,
            )
        )
    return result


@router.patch("/cabinets/{cabinet_id}/status", response_model=MessageResponse)
def update_cabinet_status(
    cabinet_id: str,
    data: CabinetStatusUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    cabinet.status = (
        CabinetStatus.ACTIVE if data.status == "active" else CabinetStatus.SUSPENDED
    )
    if data.status == "active":
        members = db.query(User).filter(User.cabinet_id == cabinet.id).all()
        for m in members:
            if m.is_verified:
                m.is_active = True
    log_audit(db, f"admin.cabinet_{data.status}", user=user, request=request, details=cabinet.name)
    db.commit()

    action = "activé" if data.status == "active" else "suspendu"
    return MessageResponse(message=f"Cabinet {cabinet.name} {action} avec succès.")


@router.patch("/cabinets/{cabinet_id}/approve", response_model=MessageResponse)
def approve_cabinet(
    cabinet_id: str,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    cabinet.status = CabinetStatus.ACTIVE
    members = db.query(User).filter(User.cabinet_id == cabinet.id).all()
    for m in members:
        if m.is_verified:
            m.is_active = True

    log_audit(db, "admin.cabinet_approve", user=user, request=request, details=cabinet.name)
    db.commit()
    return MessageResponse(message=f"Cabinet {cabinet.name} approuvé et activé.")


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_metrics(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    active = (
        db.query(Cabinet)
        .filter(Cabinet.status == CabinetStatus.ACTIVE, Cabinet.name != "WebVoice Platform")
        .count()
    )
    suspended = (
        db.query(Cabinet)
        .filter(Cabinet.status == CabinetStatus.SUSPENDED, Cabinet.name != "WebVoice Platform")
        .count()
    )
    total_users = db.query(User).filter(User.role != UserRole.ADMIN_WEBVOICE).count()
    total_docs = db.query(Document).count()
    ai_today = (
        db.query(AuditLog)
        .filter(
            AuditLog.created_at >= today_start,
            AuditLog.action.in_(
                (
                    "document.summarize",
                    "document.summarize_degraded",
                    "case.analyse",
                    "document.synthesize",
                )
            ),
        )
        .count()
    )
    avg_ocr = db.query(func.avg(Document.ocr_score)).scalar() or 0

    return AdminMetricsResponse(
        active_cabinets=active,
        suspended_cabinets=suspended,
        total_users=total_users,
        total_documents=total_docs,
        ai_actions_today=ai_today,
        avg_ocr_score=round(float(avg_ocr), 1),
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = 50,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 200)).all()
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            cabinet_id=log.cabinet_id,
            action=log.action,
            ip_address=log.ip_address,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post("/corpus/reindex")
def reindex_corpus(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    from app.services.rag import get_corpus_stats, reindex_all_corpus

    stats = reindex_all_corpus()
    log_audit(db, "admin.corpus_reindex", user=user, request=request, details=str(stats))
    db.commit()
    return {"message": "Corpus réindexé", "stats": stats, "overview": get_corpus_stats()}

