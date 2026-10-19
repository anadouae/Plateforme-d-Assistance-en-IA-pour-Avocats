"""Purge complète d'un cabinet (admin plateforme uniquement)."""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    ActivityArchive,
    AgendaEvent,
    AuditLog,
    AuthSession,
    BillingInvoice,
    Cabinet,
    CabinetInvite,
    CabinetNotification,
    CabinetReferral,
    CabinetSubscription,
    Case,
    Document,
    EmailToken,
    MfaRecoveryCode,
    PlaidoirieDraft,
    PlaidoirieRevision,
    SubscriptionEvent,
    UsageCounter,
    User,
)

logger = logging.getLogger(__name__)

PROTECTED_CABINET_NAMES = {"WebVoice Platform"}


def purge_cabinet(db: Session, cabinet_id: str) -> dict:
    """Supprime définitivement un cabinet et toutes ses données liées."""
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cab:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")
    if cab.name in PROTECTED_CABINET_NAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce cabinet plateforme ne peut pas être supprimé.",
        )

    name = cab.name
    stats = {
        "cabinet_id": cabinet_id,
        "cabinet_name": name,
        "documents": 0,
        "cases": 0,
        "users": 0,
    }

    try:
        # —— Pièces (stockage + index) ——
        from app.services.rag import delete_document_index
        from app.services.storage import delete_file

        docs = db.query(Document).filter(Document.cabinet_id == cabinet_id).all()
        for doc in docs:
            try:
                delete_document_index(doc.cabinet_id, doc.case_id, doc.id)
            except Exception:
                logger.warning("Index skip %s", doc.id)
            try:
                delete_file(doc.storage_path)
            except Exception:
                logger.warning("Storage skip %s", doc.id)
            db.delete(doc)
            stats["documents"] += 1

        # —— Contenu dossiers (ordre FK) ——
        db.query(AgendaEvent).filter(AgendaEvent.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        # Révisions AVANT brouillons (FK draft_id)
        db.query(PlaidoirieRevision).filter(PlaidoirieRevision.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(PlaidoirieDraft).filter(PlaidoirieDraft.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )

        cases = db.query(Case).filter(Case.cabinet_id == cabinet_id).all()
        for case in cases:
            db.delete(case)
            stats["cases"] += 1

        # —— Équipe / collab ——
        db.query(CabinetNotification).filter(CabinetNotification.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(CabinetInvite).filter(CabinetInvite.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(ActivityArchive).filter(ActivityArchive.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )

        # —— Utilisateurs (+ tokens e-mail / sessions) ——
        users = db.query(User).filter(User.cabinet_id == cabinet_id).all()
        user_ids = [u.id for u in users]
        if user_ids:
            db.query(EmailToken).filter(EmailToken.user_id.in_(user_ids)).delete(
                synchronize_session=False
            )
            db.query(AuthSession).filter(AuthSession.user_id.in_(user_ids)).delete(
                synchronize_session=False
            )
            db.query(MfaRecoveryCode).filter(MfaRecoveryCode.user_id.in_(user_ids)).delete(
                synchronize_session=False
            )
        for u in users:
            db.delete(u)
            stats["users"] += 1

        # —— Billing ——
        db.query(SubscriptionEvent).filter(SubscriptionEvent.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(BillingInvoice).filter(BillingInvoice.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(UsageCounter).filter(UsageCounter.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )
        db.query(CabinetSubscription).filter(CabinetSubscription.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )

        # —— Parrainage ——
        db.query(CabinetReferral).filter(
            (CabinetReferral.referrer_cabinet_id == cabinet_id)
            | (CabinetReferral.referee_cabinet_id == cabinet_id)
        ).delete(synchronize_session=False)
        db.query(Cabinet).filter(Cabinet.referred_by_cabinet_id == cabinet_id).update(
            {Cabinet.referred_by_cabinet_id: None}, synchronize_session=False
        )

        db.query(AuditLog).filter(AuditLog.cabinet_id == cabinet_id).delete(
            synchronize_session=False
        )

        db.delete(cab)
        db.flush()
        return stats
    except IntegrityError as exc:
        db.rollback()
        logger.exception("Purge IntegrityError cabinet=%s", cabinet_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Suppression bloquée par une contrainte base de données. "
                "Réessayez ; si le problème continue, contactez le support technique."
            ),
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Purge SQLAlchemyError cabinet=%s", cabinet_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du cabinet « {name} ».",
        ) from exc
