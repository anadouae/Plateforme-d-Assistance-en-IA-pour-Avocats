from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import log_audit, require_roles
from app.core.database import get_db
from app.models import AuditLog, Cabinet, CabinetStatus, Case, Document, User, UserRole
from app.schemas import (
    AdminBillingEventOut,
    AdminCabinetDetailResponse,
    AdminCabinetResponse,
    AdminCabinetUserResponse,
    AdminInvoiceOut,
    AdminMetricsResponse,
    AdminSubscriptionSnapshot,
    AdminUserStatusUpdate,
    AuditLogResponse,
    CabinetDeleteRequest,
    CabinetStatusUpdate,
    MessageResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _cabinet_row(db: Session, cab: Cabinet) -> AdminCabinetResponse:
    return AdminCabinetResponse(
        id=cab.id,
        name=cab.name,
        city=cab.city,
        address=cab.address,
        barreau=cab.barreau,
        ice=cab.ice,
        status=cab.status.value,
        user_count=db.query(User).filter(
            User.cabinet_id == cab.id,
            ~User.email.like("%@deleted.lexhub.invalid"),
        ).count(),
        document_count=db.query(Document).filter(Document.cabinet_id == cab.id).count(),
        case_count=db.query(Case).filter(Case.cabinet_id == cab.id).count(),
        created_at=cab.created_at,
    )


def _is_deleted_account(u: User) -> bool:
    email = (u.email or "").lower()
    return email.endswith("@deleted.lexhub.invalid") or (u.full_name or "") == "Compte supprimé"


def _user_row(m: User) -> AdminCabinetUserResponse:
    return AdminCabinetUserResponse(
        id=m.id,
        email=m.email,
        full_name=m.full_name or "",
        role=m.role.value,
        phone=m.phone,
        is_active=bool(m.is_active),
        is_verified=bool(m.is_verified),
        created_at=m.created_at,
        is_deleted_account=_is_deleted_account(m),
    )


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
    return [_cabinet_row(db, cab) for cab in cabinets]


@router.get("/cabinets/{cabinet_id}", response_model=AdminCabinetDetailResponse)
def get_cabinet_detail(
    cabinet_id: str,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    cabinet = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cabinet or cabinet.name == "WebVoice Platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    base = _cabinet_row(db, cabinet)
    members = (
        db.query(User)
        .filter(User.cabinet_id == cabinet.id)
        .order_by(User.created_at.asc())
        .all()
    )
    active_users = [_user_row(m) for m in members if not _is_deleted_account(m)]
    deleted_users = [_user_row(m) for m in members if _is_deleted_account(m)]

    subscription = None
    billing_history = []
    invoices_out = []
    try:
        from app.services import billing as billing_svc
        from app.models import SubscriptionPlan, BillingInvoice

        sub = billing_svc.ensure_subscription(db, cabinet.id)
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
        subscription = AdminSubscriptionSnapshot(
            plan_slug=plan.slug if plan else None,
            plan_name=plan.name if plan else None,
            status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
            billing_cycle=sub.billing_cycle.value
            if hasattr(sub.billing_cycle, "value")
            else str(sub.billing_cycle),
            trial_ends_at=sub.trial_ends_at,
            current_period_end=sub.current_period_end,
            cancel_at_period_end=bool(sub.cancel_at_period_end),
            cancel_reason_code=sub.cancel_reason_code,
            cancel_reason_text=sub.cancel_reason_text,
            cancel_requested_at=sub.cancel_requested_at,
            payment_provider=sub.payment_provider,
        )
        billing_history = [
            AdminBillingEventOut(
                event_type=e.event_type,
                plan_slug=e.plan_slug,
                detail=e.detail,
                created_at=e.created_at,
            )
            for e in billing_svc.list_events(db, cabinet.id, limit=30)
        ]
        inv_rows = (
            db.query(BillingInvoice)
            .filter(BillingInvoice.cabinet_id == cabinet.id)
            .order_by(BillingInvoice.created_at.desc())
            .limit(40)
            .all()
        )
        for i in inv_rows:
            st = (i.status or "").lower()
            kind = (
                "trial_receipt"
                if int(i.amount_mad or 0) == 0 or "trial" in st or "essai" in st
                else "invoice"
            )
            invoices_out.append(
                AdminInvoiceOut(
                    id=i.id,
                    number=i.number,
                    plan_name=i.plan_name,
                    amount_mad=int(i.amount_mad or 0),
                    status=i.status,
                    billing_cycle=i.billing_cycle,
                    issued_at=i.issued_at or i.created_at,
                    kind=kind,
                )
            )
        db.commit()
    except Exception:
        db.rollback()

    return AdminCabinetDetailResponse(
        **base.model_dump(),
        users=active_users,
        deleted_accounts_count=len(deleted_users),
        deleted_accounts=deleted_users,
        subscription=subscription,
        billing_history=billing_history,
        invoices=invoices_out,
    )

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

    members = db.query(User).filter(User.cabinet_id == cabinet.id).all()
    cabinet.status = (
        CabinetStatus.ACTIVE if data.status == "active" else CabinetStatus.SUSPENDED
    )
    if data.status == "active":
        for m in members:
            if m.is_verified:
                m.is_active = True
    else:
        for m in members:
            m.is_active = False

    log_audit(db, f"admin.cabinet_{data.status}", user=user, request=request, details=cabinet.name)
    db.commit()

    action = "activé" if data.status == "active" else "suspendu"
    return MessageResponse(message=f"Cabinet {cabinet.name} {action} avec succès.")


@router.post("/cabinets/{cabinet_id}/purge", response_model=MessageResponse)
def purge_cabinet_endpoint(
    cabinet_id: str,
    data: CabinetDeleteRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    """Suppression définitive d'un cabinet client (admin plateforme uniquement)."""
    conf = (data.confirmation or "").strip().upper()
    if conf not in {"SUPPRIMER", "DELETE", "حذف"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Saisissez SUPPRIMER pour confirmer (ou DELETE / حذف).',
        )

    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cab or cab.name == "WebVoice Platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cabinet introuvable")

    from app.services.cabinet_purge import purge_cabinet
    from app.services.storage import delete_file

    if cab.logo_path:
        try:
            delete_file(cab.logo_path)
        except Exception:
            pass

    log_audit(
        db,
        "admin.cabinet_delete",
        user=user,
        request=request,
        details=f"{cab.name}|{cabinet_id}",
    )
    db.flush()
    stats = purge_cabinet(db, cabinet_id)
    db.commit()
    return MessageResponse(
        message=(
            f"Cabinet « {stats['cabinet_name']} » supprimé définitivement "
            f"({stats['users']} comptes, {stats['cases']} dossiers, {stats['documents']} pièces)."
        )
    )


@router.patch("/users/{user_id}/status", response_model=MessageResponse)
def update_user_status(
    user_id: str,
    data: AdminUserStatusUpdate,
    request: Request,
    admin: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target or target.role == UserRole.ADMIN_WEBVOICE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    target.is_active = data.is_active
    log_audit(
        db,
        "admin.user_activate" if data.is_active else "admin.user_deactivate",
        user=admin,
        request=request,
        details=f"{target.email} ({target.full_name})",
    )
    db.commit()
    verb = "activé" if data.is_active else "désactivé"
    return MessageResponse(message=f"Compte {target.email} {verb}.")


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_metrics(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
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
    total_users = (
        db.query(User)
        .filter(
            User.role != UserRole.ADMIN_WEBVOICE,
            ~User.email.like("%@deleted.lexhub.invalid"),
        )
        .count()
    )
    total_docs = db.query(Document).count()
    deleted_accounts = (
        db.query(User).filter(User.email.like("%@deleted.lexhub.invalid")).count()
    )
    cancel_requests = 0
    try:
        from app.models import CabinetSubscription

        cancel_requests = (
            db.query(CabinetSubscription)
            .filter(CabinetSubscription.cancel_at_period_end.is_(True))
            .count()
        )
    except Exception:
        pass

    return AdminMetricsResponse(
        active_cabinets=active,
        suspended_cabinets=suspended,
        total_users=total_users,
        total_documents=total_docs,
        deleted_accounts=deleted_accounts,
        cancel_requests=cancel_requests,
    )


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = 200,
    q: str | None = None,
    action: str | None = None,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    try:
        from app.services.admin_audit_archive import maybe_archive_old_admin_audit

        maybe_archive_old_admin_audit(db, force=False)
    except Exception:
        pass

    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action and action.strip():
        prefix = action.strip().lower()
        query = query.filter(AuditLog.action.ilike(f"{prefix}%"))
    logs = query.limit(min(max(limit, 1), 200)).all()

    user_ids = {log.user_id for log in logs if log.user_id}
    cabinet_ids = {log.cabinet_id for log in logs if log.cabinet_id}
    users_by_id = {
        u.id: u
        for u in (
            db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        )
    }
    cabinets_by_id = {
        c.id: c
        for c in (
            db.query(Cabinet).filter(Cabinet.id.in_(cabinet_ids)).all() if cabinet_ids else []
        )
    }

    needle = (q or "").strip().lower()
    out: list[AuditLogResponse] = []
    for log in logs:
        u = users_by_id.get(log.user_id) if log.user_id else None
        cab = cabinets_by_id.get(log.cabinet_id) if log.cabinet_id else None
        row = AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            cabinet_id=log.cabinet_id,
            action=log.action,
            ip_address=log.ip_address,
            details=log.details,
            created_at=log.created_at,
            user_name=(u.full_name if u else None),
            user_email=(u.email if u else None),
            cabinet_name=(cab.name if cab else None),
        )
        if needle:
            hay = " ".join(
                filter(
                    None,
                    [
                        row.action,
                        row.details,
                        row.user_name,
                        row.user_email,
                        row.cabinet_name,
                        row.ip_address,
                    ],
                )
            ).lower()
            if needle not in hay:
                continue
        out.append(row)
    return out


@router.get("/audit-archives")
def list_audit_archives(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    from app.models import AdminAuditArchive

    rows = (
        db.query(AdminAuditArchive)
        .order_by(AdminAuditArchive.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "period_start": r.period_start,
            "period_end": r.period_end,
            "row_count": r.row_count,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/audit-archives/{archive_id}/download")
def download_audit_archive(
    archive_id: str,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response

    from app.models import AdminAuditArchive
    from app.services.admin_audit_archive import admin_audit_archive_bytes

    row = db.query(AdminAuditArchive).filter(AdminAuditArchive.id == archive_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archive introuvable")
    data = admin_audit_archive_bytes(row)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{row.filename}"'},
    )


@router.post("/audit-archives/run")
def run_audit_archive(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    from app.services.admin_audit_archive import maybe_archive_old_admin_audit

    archive = maybe_archive_old_admin_audit(db, force=True)
    if not archive:
        return {"message": "Aucun log éligible à archiver (> 90 j)", "archived": False}
    log_audit(
        db,
        "admin.audit_archive",
        user=user,
        request=request,
        details=f"{archive.row_count} lignes",
    )
    db.commit()
    return {
        "message": f"Archive créée ({archive.row_count} lignes)",
        "archived": True,
        "id": archive.id,
        "filename": archive.filename,
    }


# Même filtre que /metrics et /cabinets — jamais compter le cabinet interne ops.
_PLATFORM_CABINET_NAME = "WebVoice Platform"


@router.post("/platform-analysis")
def platform_activity_analysis(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    """Rapport owner : mêmes bases que le tableau de bord + pistes de gains."""
    from datetime import datetime, timezone, timedelta
    from collections import defaultdict
    from sqlalchemy import func
    from app.models import CabinetSubscription, SubscriptionPlan, UsageCounter

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=30)
    client_cab_filter = Cabinet.name != _PLATFORM_CABINET_NAME

    # —— Aligné strictement sur GET /api/admin/metrics ——
    cabinets_actifs = (
        db.query(Cabinet)
        .filter(Cabinet.status == CabinetStatus.ACTIVE, client_cab_filter)
        .count()
    )
    cabinets_suspendus = (
        db.query(Cabinet)
        .filter(Cabinet.status == CabinetStatus.SUSPENDED, client_cab_filter)
        .count()
    )
    users = (
        db.query(User)
        .filter(
            User.role != UserRole.ADMIN_WEBVOICE,
            ~User.email.like("%@deleted.lexhub.invalid"),
        )
        .count()
    )
    cases = (
        db.query(Case)
        .join(Cabinet, Case.cabinet_id == Cabinet.id)
        .filter(client_cab_filter)
        .count()
    )
    # Même base que GET /metrics (total_documents) — tous les documents indexés
    docs = db.query(Document).count()

    client_ids = {r[0] for r in db.query(Cabinet.id).filter(client_cab_filter).all()}

    logins_30d = (
        db.query(AuditLog)
        .filter(AuditLog.action == "auth.login_success", AuditLog.created_at >= since)
        .count()
    )

    ym = now.strftime("%Y-%m")
    usage_rows = [
        r
        for r in db.query(UsageCounter).filter(UsageCounter.period_ym == ym).all()
        if r.cabinet_id in client_ids
    ]
    ai_credits = sum(int(getattr(r, "ai_credits_used", 0) or 0) for r in usage_rows)
    pleas = sum(int(getattr(r, "plaidoiries_count", 0) or 0) for r in usage_rows)

    plans = db.query(SubscriptionPlan).all()
    plan_by_id = {p.id: p for p in plans}
    plans_by_slug = {p.slug: p for p in plans}

    subs = [
        s for s in db.query(CabinetSubscription).all() if s.cabinet_id in client_ids
    ]
    by_status: dict[str, int] = {}
    for s in subs:
        st = getattr(s.status, "value", str(s.status))
        by_status[st] = by_status.get(st, 0) + 1

    status_labels = {
        "trial": "essai",
        "active": "actif",
        "past_due": "impayé",
        "canceled": "résilié",
        "expired": "expiré",
    }
    abo_fr = ", ".join(
        f"{n} {status_labels.get(k, k)}" for k, n in sorted(by_status.items(), key=lambda x: -x[1])
    ) or "aucun"

    # Villes = même périmètre que la liste cabinets du dashboard
    city_rows = (
        db.query(Cabinet.city, func.count(Cabinet.id))
        .filter(client_cab_filter)
        .group_by(Cabinet.city)
        .all()
    )
    par_ville: dict[str, int] = {}
    for city, n in city_rows:
        label = (city or "").strip() or "—"
        par_ville[label] = int(n)

    credits_par_plan: dict[str, int] = defaultdict(int)
    plaidoiries_par_plan: dict[str, int] = defaultdict(int)
    sub_by_cab = {s.cabinet_id: s for s in subs}
    for row in usage_rows:
        sub = sub_by_cab.get(row.cabinet_id)
        if sub and sub.plan_id in plan_by_id:
            slug = plan_by_id[sub.plan_id].slug
        else:
            slug = "sans_abo"
        credits_par_plan[slug] += int(getattr(row, "ai_credits_used", 0) or 0)
        plaidoiries_par_plan[slug] += int(getattr(row, "plaidoiries_count", 0) or 0)

    recommendations: list[str] = []
    trial_n = by_status.get("trial", 0)
    active_n = by_status.get("active", 0)
    past = by_status.get("past_due", 0)
    if trial_n:
        recommendations.append(f"{trial_n} cabinet(s) en essai.")
    if active_n:
        recommendations.append(f"{active_n} abonnement(s) actif(s).")
    if past:
        recommendations.append(f"{past} abonnement(s) impayé(s).")
    if cabinets_suspendus:
        recommendations.append(f"{cabinets_suspendus} cabinet(s) suspendu(s).")
    recommendations.append(
        f"Mois en cours : {pleas} plaidoirie(s), {ai_credits} crédit(s) IA."
    )
    recommendations.append(f"30 jours : {logins_30d} connexion(s) réussie(s).")
    recommendations.append(
        f"Stock clients : {cases} dossier(s), {docs} document(s) "
        f"— {cabinets_actifs} cabinet(s) actif(s), {users} utilisateur(s)."
    )
    if par_ville:
        top_city, top_n = max(par_ville.items(), key=lambda x: x[1])
        recommendations.append(f"Ville la plus représentée : {top_city} ({top_n}).")
    if credits_par_plan:
        top_plan, top_c = max(credits_par_plan.items(), key=lambda x: x[1])
        recommendations.append(
            f"Crédits IA ce mois — plan le plus consommateur : {top_plan} ({top_c})."
        )

    def tip(titre: str, en_clair: str, action: str) -> dict[str, str]:
        return {"titre": titre, "en_clair": en_clair, "action": action}

    from app.services.ops_coach import (
        attach_targets_with_drafts,
        sort_tips,
        tip_card,
    )

    cab_by_id = {
        c.id: c
        for c in db.query(Cabinet).filter(client_cab_filter).all()
    }

    growth: list[dict] = []
    cancel_subs = [s for s in subs if bool(getattr(s, "cancel_at_period_end", False))]
    cancel_n = len(cancel_subs)
    trial_subs = [
        s for s in subs if getattr(s.status, "value", str(s.status)) == "trial"
    ]
    trials_ending_subs = []
    for s in trial_subs:
        ends = getattr(s, "trial_ends_at", None)
        if ends is None:
            continue
        try:
            delta = (ends - now).days
        except TypeError:
            continue
        if 0 <= delta <= 7:
            trials_ending_subs.append((s, delta))

    past_subs = [
        s for s in subs if getattr(s.status, "value", str(s.status)) == "past_due"
    ]

    if trial_n:
        ids = [s.cabinet_id for s in trial_subs]
        growth.append(
            tip_card(
                tip_id="trial_convert",
                scenario="trial_convert",
                priority="high",
                action_type="email",
                titre="Cabinet encore en essai gratuit",
                en_clair=(
                    f"{trial_n} cabinet teste LexHub gratis (plan essai). "
                    "L’email sert à l’accompagner avant la fin de l’essai, "
                    "pour qu’il passe éventuellement à un plan payant — sinon il part sans rien payer."
                ),
                action="Optionnel : envoyer un email d’accompagnement (pas obligatoire). Objectif = conversion essai → payant.",
                why=[
                    f"{trial_n} abonnement(s) en statut essai (= gratuit pour le moment)",
                    "Sans relance, beaucoup d’essais se terminent sans abonnement",
                    "Ce n’est pas une facture : c’est un rappel d’aide + proposition de plan",
                ],
                sequence=["J0 : email conversion", "J+3 : rappel si pas de réponse", "J-1 fin essai : appel"],
                targets=attach_targets_with_drafts(db, scenario="trial_convert", cabinet_ids=ids),
            )
        )
    if trials_ending_subs:
        ids = [s.cabinet_id for s, _ in trials_ending_subs]
        extra = {
            s.cabinet_id: {"days_left": d} for s, d in trials_ending_subs
        }
        growth.append(
            tip_card(
                tip_id="trial_ending",
                scenario="trial_ending",
                priority="high",
                action_type="email",
                titre="Essai bientôt terminé",
                en_clair=f"{len(trials_ending_subs)} essai se termine dans moins d’une semaine.",
                action="Relancer immédiatement pour éviter la perte du cabinet.",
                why=["Fin d’essai ≤ 7 jours", "Risque élevé de churn gratuit"],
                sequence=["Aujourd’hui : email urgent", "Demain : suivi téléphonique"],
                targets=attach_targets_with_drafts(
                    db, scenario="trial_ending", cabinet_ids=ids, extra_by_cab=extra
                ),
            )
        )
    if past:
        ids = [s.cabinet_id for s in past_subs]
        growth.append(
            tip_card(
                tip_id="past_due",
                scenario="past_due",
                priority="high",
                action_type="email",
                titre="Paiement en retard",
                en_clair=f"{past} cabinet n’a pas réglé son abonnement.",
                action="Envoyer un rappel de règlement (email) et suivre le paiement.",
                why=[f"{past} abonnement(s) impayé(s)", "Impact direct sur le revenu"],
                sequence=["J0 : email rappel", "J+2 : second rappel", "J+5 : appel"],
                targets=attach_targets_with_drafts(db, scenario="past_due", cabinet_ids=ids),
                internal_href="/admin/plans",
            )
        )
    if cancel_n:
        ids = [s.cabinet_id for s in cancel_subs]
        growth.append(
            tip_card(
                tip_id="cancel_retain",
                scenario="cancel_retain",
                priority="high",
                action_type="email",
                titre="Un cabinet veut partir",
                en_clair=f"{cancel_n} cabinet a demandé l’arrêt en fin de période.",
                action="Proposer un plan adapté ou un pack crédits avant le départ.",
                why=["Résiliation programmée (cancel_at_period_end)", "Dernière chance de rétention"],
                sequence=["J0 : email rétention", "J+2 : appel", "Offre plan / crédits"],
                targets=attach_targets_with_drafts(db, scenario="cancel_retain", cabinet_ids=ids),
            )
        )

    solo = plans_by_slug.get("solo")
    higher = (
        plans_by_slug.get("cabinet")
        or plans_by_slug.get("team")
        or plans_by_slug.get("cabinet_pro")
        or plans_by_slug.get("pro")
    )
    higher_label = {
        "pro": "Pro",
        "cabinet": "Cabinet",
        "team": "Équipe",
        "cabinet_pro": "Cabinet Pro",
    }
    solo_subs = [
        s
        for s in subs
        if s.plan_id in plan_by_id
        and plan_by_id[s.plan_id].slug == "solo"
        and getattr(s.status, "value", str(s.status)) in ("active", "trial")
    ]
    if solo and higher and solo_subs:
        delta_price = int(higher.price_mad_monthly or 0) - int(solo.price_mad_monthly or 0)
        hl = higher_label.get(higher.slug, higher.slug)
        if delta_price > 0:
            ids = [s.cabinet_id for s in solo_subs]
            extra = {cid: {"plan_label": hl, "delta_mad": delta_price} for cid in ids}
            growth.append(
                tip_card(
                    tip_id="upsell_solo",
                    scenario="upsell_solo",
                    priority="medium",
                    action_type="email",
                    titre="Passer du plan Solo au plan supérieur",
                    en_clair=(
                        f"{len(solo_subs)} cabinet sur Solo — "
                        f"le plan {hl} rapporte +{delta_price} MAD/mois chacun."
                    ),
                    action=f"Proposer le plan {hl} par email (ou appel commercial).",
                    why=[
                        f"{len(solo_subs)} sur Solo",
                        f"Upsell potentiel +{delta_price} MAD/mois / cabinet",
                    ],
                    sequence=["Email upsell", "Si intérêt : démo 15 min", "Assigner plan dans admin"],
                    targets=attach_targets_with_drafts(
                        db, scenario="upsell_solo", cabinet_ids=ids, extra_by_cab=extra
                    ),
                    internal_href="/admin/plans",
                )
            )

    heavy_ids: list[str] = []
    for s in solo_subs:
        used = next(
            (
                int(getattr(r, "ai_credits_used", 0) or 0)
                for r in usage_rows
                if r.cabinet_id == s.cabinet_id
            ),
            0,
        )
        if used >= 20:
            heavy_ids.append(s.cabinet_id)
    if heavy_ids:
        growth.append(
            tip_card(
                tip_id="heavy_usage",
                scenario="heavy_usage",
                priority="medium",
                action_type="email",
                titre="Beaucoup d’IA sur un petit plan",
                en_clair=f"{len(heavy_ids)} cabinet Solo consomme déjà beaucoup de crédits IA.",
                action="Proposer un plan plus grand ou des crédits à la demande.",
                why=["Usage IA élevé sur Solo (≥ 20 crédits)", "Bon moment pour monétiser"],
                sequence=["Email usage", "Offre pack crédits / plan"],
                targets=attach_targets_with_drafts(db, scenario="heavy_usage", cabinet_ids=heavy_ids),
            )
        )

    unpaid_active_ids = []
    if cabinets_actifs and active_n < cabinets_actifs:
        paid_ids = {
            s.cabinet_id
            for s in subs
            if getattr(s.status, "value", str(s.status)) == "active"
        }
        for cid, cab in cab_by_id.items():
            if cab.status == CabinetStatus.ACTIVE and cid not in paid_ids:
                unpaid_active_ids.append(cid)
        growth.append(
            tip_card(
                tip_id="activate_billing",
                scenario="activate_billing",
                priority="medium",
                action_type="email",
                titre="Cabinet actif qui ne paie pas encore",
                en_clair=(
                    f"{len(unpaid_active_ids)} cabinet(s) actif(s) sans abonnement payant "
                    "(souvent encore en essai)."
                ),
                action="Aider à activer un plan payant dans LexHub.",
                why=[
                    f"{cabinets_actifs} cabinets actifs",
                    f"{active_n} abonnements payants actifs",
                ],
                sequence=["Email activation", "Suivi dans /admin/cabinets"],
                targets=attach_targets_with_drafts(
                    db, scenario="activate_billing", cabinet_ids=unpaid_active_ids
                ),
                internal_href="/admin/cabinets",
            )
        )

    if pleas == 0 and cabinets_actifs:
        active_ids = [
            cid for cid, cab in cab_by_id.items() if cab.status == CabinetStatus.ACTIVE
        ]
        growth.append(
            tip_card(
                tip_id="first_plea",
                scenario="first_plea",
                priority="medium",
                action_type="email",
                titre="Peu d’usage de la plaidoirie",
                en_clair="Aucune plaidoirie comptabilisée ce mois-ci.",
                action="Guider les cabinets pour lancer une première plaidoirie.",
                why=["0 plaidoirie ce mois", "L’usage précède le renouvellement"],
                sequence=["Email onboarding", "Tutoriel / démo"],
                targets=attach_targets_with_drafts(db, scenario="first_plea", cabinet_ids=active_ids[:5]),
            )
        )
    elif ai_credits == 0 and pleas > 0:
        growth.append(
            tip_card(
                tip_id="credits_tracking",
                scenario="credits_tracking",
                priority="low",
                action_type="ops",
                titre="Plaidoiries faites, mais peu de crédits débités",
                en_clair=(
                    f"{pleas} plaidoirie(s) ce mois, mais 0 crédit IA sur les compteurs."
                ),
                action="Vérifier le tracking d’usage côté admin (pas un email client).",
                why=[
                    f"{pleas} plaidoiries comptées",
                    "0 crédit IA — possible écart de tracking",
                ],
                sequence=["Vérifier compteurs UsageCounter", "Corriger si besoin", "Puis vendre packs"],
                targets=[],
                internal_href="/admin/plans",
                cta_label="Ouvrir Plans & quotas",
            )
        )

    if not growth:
        growth.append(
            tip_card(
                tip_id="healthy",
                scenario="healthy",
                priority="low",
                action_type="watch",
                titre="Situation correcte pour l’instant",
                en_clair="Pas d’alerte urgente sur les abonnements.",
                action="Surveiller les essais et les plafonds Solo.",
                why=["Aucun signal critique détecté"],
                sequence=["Revue hebdo Ops Coach"],
                targets=[],
            )
        )

    from app.services.email import email_configured as _email_ok

    growth = sort_tips(growth)

    report = {
        "generated_at": now.isoformat(),
        "period_days": 30,
        "aligned_with": "admin_metrics_cabinets_list",
        "metrics": {
            "cabinets_actifs": cabinets_actifs,
            "cabinets_suspendus": cabinets_suspendus,
            "utilisateurs": users,
            "dossiers": cases,
            "documents": docs,
            "connexions_30j": logins_30d,
            "plaidoiries_mois": pleas,
            "credits_ia_mois": ai_credits,
            "abonnements_par_statut": by_status,
            "par_ville": par_ville,
            "credits_par_plan": dict(credits_par_plan),
            "plaidoiries_par_plan": dict(plaidoiries_par_plan),
        },
        "recommendations": recommendations,
        "growth_recommendations": growth,
        "ops_coach": {
            "version": "v2",
            "email_ready": _email_ok(),
            "legend": {
                "email": "Préparer / modifier / envoyer un email",
                "ops": "Action technique interne (pas d’email client)",
                "billing": "Facturation",
                "call": "Contact téléphonique",
                "watch": "Surveillance uniquement",
            },
        },
        "summary_fr": (
            f"LexHub (cabinets clients) : {cabinets_actifs} actif(s), {users} utilisateur(s). "
            f"30 jours : {logins_30d} connexions. "
            f"Mois en cours : {pleas} plaidoirie(s), {ai_credits} crédit(s) IA. "
            f"Abonnements : {abo_fr}."
        ),
    }
    log_audit(db, "admin.platform_analysis", user=user, request=request, details="Rapport d’activité généré")
    db.commit()
    return report


@router.post("/ops-coach/draft-email")
def ops_coach_draft_email(
    request: Request,
    body: dict,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    """Régénère un brouillon email pour un scénario + cabinet (modifiable ensuite)."""
    from app.services.ops_coach import attach_targets_with_drafts, build_email_draft

    scenario = str(body.get("scenario") or "").strip()
    cabinet_id = str(body.get("cabinet_id") or "").strip()
    if not scenario or not cabinet_id:
        raise HTTPException(status_code=400, detail="scenario et cabinet_id requis")
    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id, Cabinet.name != _PLATFORM_CABINET_NAME).first()
    if not cab:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    targets = attach_targets_with_drafts(
        db,
        scenario=scenario,
        cabinet_ids=[cabinet_id],
        extra_by_cab={cabinet_id: body.get("extra") or {}},
    )
    if not targets:
        raise HTTPException(status_code=404, detail="Impossible de préparer la cible")
    t = targets[0]
    if not t.get("draft"):
        # pas de contact → brouillon générique à compléter
        t["draft"] = build_email_draft(
            scenario=scenario,
            cabinet_name=cab.name,
            contact_name="Maître",
            extra=body.get("extra") or {},
        )
    log_audit(
        db,
        "admin.ops_coach_draft",
        user=user,
        request=request,
        details=f"Brouillon email ({scenario}) — cabinet « {cab.name} »",
    )
    db.commit()
    return t


@router.post("/ops-coach/send-email")
def ops_coach_send_email(
    request: Request,
    body: dict,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    """Envoi email Ops Coach après validation humaine (objet + corps éditables)."""
    from app.services.email import email_configured
    from app.services.ops_coach import send_ops_email

    to = str(body.get("to") or "").strip()
    subject = str(body.get("subject") or "").strip()
    body_text = str(body.get("body_text") or "").strip()
    body_html = (body.get("body_html") or None)
    if isinstance(body_html, str):
        body_html = body_html.strip() or None
    else:
        body_html = None
    cc_raw = body.get("cc") or []
    cc = [str(x).strip() for x in cc_raw if str(x).strip()] if isinstance(cc_raw, list) else []
    tip_id = str(body.get("tip_id") or "")
    cabinet_id = str(body.get("cabinet_id") or "")

    if not to or "@" not in to:
        raise HTTPException(status_code=400, detail="Destinataire email invalide")
    if not subject or not body_text:
        raise HTTPException(status_code=400, detail="Objet et corps requis")
    if not email_configured():
        raise HTTPException(
            status_code=503,
            detail="Envoi email non configuré sur le serveur (Resend/SMTP).",
        )

    ok = send_ops_email(
        to=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        cc=cc,
    )
    if not ok:
        raise HTTPException(status_code=502, detail="Échec d’envoi email")

    cab_name = ""
    if cabinet_id:
        cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
        cab_name = cab.name if cab else ""
    log_audit(
        db,
        "admin.ops_coach_send",
        user=user,
        request=request,
        details=(
            f"Email Ops Coach envoyé à {to}"
            + (f" (cabinet « {cab_name} »)" if cab_name else "")
            + f" — « {subject[:80]} »"
            + (f" [{tip_id}]" if tip_id else "")
        ),
    )
    db.commit()
    return {
        "message": f"Email envoyé à {to}" + (f" (cc: {', '.join(cc)})" if cc else ""),
        "to": to,
        "cc": cc,
        "subject": subject,
    }


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
