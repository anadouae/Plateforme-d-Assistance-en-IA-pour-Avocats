"""API abonnements / plans LexHub (paiement réel = phase 2, mock manuel)."""

import json
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit, require_cabinet_billing_admin, require_roles
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.core.database import get_db
from app.models import CommercialLead, PaymentTransferRequest, SubscriptionPlan, User, UserRole
from app.schemas import MessageResponse, PaymentTransferCreate, PaymentTransferResponse
from app.services import billing as billing_svc
from app.services.cle_de_barre import generate_cle_de_barre

router = APIRouter(prefix="/api/billing", tags=["billing"])


class CommercialLeadIn(BaseModel):
    kind: Literal["enterprise_trial", "custom"]
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=40)
    cabinet_name: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=120)
    lawyers_count: Optional[int] = Field(None, ge=1, le=500)
    message: Optional[str] = Field(None, max_length=4000)


@router.post("/commercial-lead")
def submit_commercial_lead(
    data: CommercialLeadIn,
    request: Request,
    db: Session = Depends(get_db),
):
    """Qualification Entreprise / Sur mesure — pas d’essai automatique."""
    check_rate_limit(request, key="billing.lead", limit=8, window_sec=3600)
    kind = data.kind
    lead = CommercialLead(
        kind=kind,
        full_name=data.full_name.strip(),
        email=data.email.strip().lower(),
        phone=(data.phone or "").strip() or None,
        cabinet_name=(data.cabinet_name or "").strip() or None,
        city=(data.city or "").strip() or None,
        lawyers_count=data.lawyers_count,
        message=(data.message or "").strip() or None,
        status="new",
    )
    db.add(lead)
    db.commit()
    try:
        from app.services.email import send_commercial_lead_email

        send_commercial_lead_email(
            kind=kind,
            full_name=lead.full_name,
            email=lead.email,
            phone=lead.phone or "",
            cabinet_name=lead.cabinet_name or "",
            city=lead.city or "",
            lawyers_count=lead.lawyers_count,
            message=lead.message or "",
        )
    except Exception:
        pass
    log_audit(
        db,
        "billing.commercial_lead",
        user=None,
        request=request,
        details=f"{kind}:{lead.email}",
    )
    db.commit()
    return {
        "ok": True,
        "message": "Demande reçue. Un conseiller vous recontacte sous 24–48 h.",
    }


class PlanOut(BaseModel):
    id: str
    slug: str
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    price_mad_monthly: int
    price_mad_yearly: int
    max_avocats: int
    max_assistants: int
    max_cases: int
    max_plaidoiries_month: int
    max_ai_credits_month: int = 50
    features: list[str]
    highlights: list[str] = []
    highlights_ar: list[str] = []
    is_public: bool
    is_recommended: bool
    is_active: bool
    sort_order: int
    trial_days: int


class SelectPlanRequest(BaseModel):
    plan_slug: str = Field(..., min_length=2, max_length=64)
    billing_cycle: str = Field("monthly", pattern="^(monthly|yearly)$")
    card_name: Optional[str] = Field(None, max_length=120)
    card_number: Optional[str] = Field(None, max_length=32)
    card_exp: Optional[str] = Field(None, max_length=7)
    card_cvc: Optional[str] = Field(None, max_length=4)


class CancelSubscriptionRequest(BaseModel):
    reason_code: str = Field(..., min_length=2, max_length=64)
    reason_text: Optional[str] = Field(None, max_length=2000)

class AdminPlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    name_ar: Optional[str] = None
    description: Optional[str] = None
    price_mad_monthly: Optional[int] = Field(None, ge=0)
    price_mad_yearly: Optional[int] = Field(None, ge=0)
    max_avocats: Optional[int] = Field(None, ge=0)
    max_assistants: Optional[int] = Field(None, ge=0)
    max_cases: Optional[int] = None
    max_plaidoiries_month: Optional[int] = None
    max_ai_credits_month: Optional[int] = Field(None, ge=0)
    features: Optional[list[str]] = None
    is_public: Optional[bool] = None
    is_recommended: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    trial_days: Optional[int] = Field(None, ge=0, le=90)


class AdminAssignPlanRequest(BaseModel):
    plan_slug: str
    status: str = Field("active", pattern="^(trial|active|canceled|expired)$")
    billing_cycle: str = Field("monthly", pattern="^(monthly|yearly)$")
    notes: Optional[str] = None


class CleDeBarreRequest(BaseModel):
    case_id: str
    extra_instructions: Optional[str] = Field(None, max_length=2000)


@router.get("/plans", response_model=list[PlanOut])
def list_public_plans(db: Session = Depends(get_db)):
    billing_svc.ensure_default_plans(db)
    db.commit()
    rows = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True), SubscriptionPlan.is_public.is_(True))
        .order_by(SubscriptionPlan.sort_order.asc())
        .all()
    )
    return [PlanOut(**billing_svc.plan_to_dict(p, public=True)) for p in rows]


@router.get("/payment-methods")
def payment_methods():
    return {
        "currency": "MAD",
        "note": "Paiement électronique en préparation — environnement LexHub déjà prêt.",
        "methods": billing_svc.MOROCCO_PAYMENT_METHODS,
    }


@router.get("/cancel-reasons")
def cancel_reasons():
    return [{"code": c, "label": lab} for c, lab in billing_svc.CANCEL_REASON_CODES]


@router.get("/entitlements")
def my_entitlements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == UserRole.ADMIN_WEBVOICE:
        return {
            "plan": {"slug": "enterprise", "name": "Plateforme WebVoice"},
            "status": "active",
            "payment_mock": True,
            "features": ["*"],
            "usage": {},
            "trial_days_left": None,
        }
    ent = billing_svc.get_entitlements(db, user.cabinet_id)
    sub = ent.subscription
    data = ent.to_dict()
    data["cancel_at_period_end"] = bool(sub.cancel_at_period_end)
    data["cancel_reason_code"] = sub.cancel_reason_code
    data["cancel_requested_at"] = (
        sub.cancel_requested_at.isoformat() if sub.cancel_requested_at else None
    )
    db.commit()
    return data


class OnDemandUpdate(BaseModel):
    enabled: bool
    mad_limit: int | None = Field(
        None,
        description="-1 = pas de plafond MAD ; 0+ = plafond mensuel en MAD ; null = ne pas changer le plafond",
    )


@router.patch("/on-demand")
def update_on_demand(
    data: OnDemandUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    """Active / désactive l’usage IA à la demande (surplus → facture)."""
    ent = billing_svc.set_on_demand_settings(
        db,
        user.cabinet_id,
        enabled=data.enabled,
        mad_limit=data.mad_limit,
    )
    log_audit(
        db,
        "billing.on_demand",
        user=user,
        request=request,
        details=f"enabled={data.enabled}:limit={data.mad_limit}",
    )
    db.commit()
    out = ent.to_dict()
    out["message"] = (
        "Usage à la demande activé — le surplus sera ajouté à la facture."
        if data.enabled
        else "Usage à la demande désactivé — aucun surplus ne sera facturé."
    )
    return out


class CreditPackPurchaseRequest(BaseModel):
    pack_id: str = Field(..., min_length=3, max_length=64)


class ExtraSeatsUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=10)


@router.get("/addons")
def billing_addons(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.cabinet_id:
        raise HTTPException(status_code=400, detail="Cabinet requis")
    return billing_svc.list_billing_addons(db, user.cabinet_id)


@router.post("/credit-packs/purchase")
def purchase_credit_pack_blocked(
    data: CreditPackPurchaseRequest,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    """Ancien endpoint — interdit (pas de crédit au clic)."""
    raise HTTPException(
        status_code=400,
        detail={
            "code": "pack_payment_required",
            "message": "Utilisez POST /credit-packs/checkout puis /credit-packs/confirm-payment.",
        },
    )


@router.post("/credit-packs/checkout")
def checkout_credit_pack(
    data: CreditPackPurchaseRequest,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    out = billing_svc.start_credit_pack_checkout(
        db, user.cabinet_id, data.pack_id, user_id=user.id
    )
    log_audit(db, "billing.credit_pack_checkout", user=user, request=request, details=data.pack_id)
    db.commit()
    return out


class CreditPackConfirmRequest(BaseModel):
    purchase_id: str = Field(..., min_length=8, max_length=64)
    card_name: str = Field(..., min_length=2, max_length=120)
    card_number: str = Field(..., min_length=13, max_length=32)
    card_exp: Optional[str] = Field(None, max_length=7)
    card_cvc: Optional[str] = Field(None, max_length=4)


@router.post("/credit-packs/confirm-payment")
def confirm_credit_pack_payment(
    data: CreditPackConfirmRequest,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    from app.models import Cabinet

    cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    ent = billing_svc.confirm_credit_pack_payment(
        db,
        user.cabinet_id,
        data.purchase_id,
        card_name=data.card_name,
        card_number=data.card_number,
        card_exp=data.card_exp,
        card_cvc=data.card_cvc,
        user_id=user.id,
        cabinet_name=cab.name if cab else "Cabinet",
    )
    log_audit(
        db,
        "billing.credit_pack_paid",
        user=user,
        request=request,
        details=data.purchase_id,
    )
    db.commit()
    out = ent.to_dict()
    out["message"] = (
        f"Paiement confirmé. Solde packs : {ent.prepaid_ai_credits} crédits "
        f"(expiration 12 mois par lot)."
    )
    return out


@router.patch("/extra-seats")
def update_extra_seats(
    data: ExtraSeatsUpdate,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    ent = billing_svc.set_extra_avocat_seats(
        db,
        user.cabinet_id,
        data.quantity,
        user_id=user.id,
    )
    log_audit(
        db,
        "billing.extra_seats",
        user=user,
        request=request,
        details=str(data.quantity),
    )
    db.commit()
    out = ent.to_dict()
    addon = data.quantity * billing_svc.EXTRA_AVOCAT_SEAT_MAD_MONTHLY
    out["message"] = (
        f"Sièges extra : {data.quantity} "
        f"(+{addon} MAD/mois sur la prochaine facture)."
        if data.quantity
        else "Aucun siège extra — retour au plafond inclus du plan Cabinet."
    )
    return out


@router.get("/insights")
def billing_insights(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Conseils contextuels (rétention / activation) pour l'UI."""
    if user.role == UserRole.ADMIN_WEBVOICE or not user.cabinet_id:
        return {"insights": []}
    from app.services.retention_lifecycle import build_smart_insights

    tips = build_smart_insights(db, user.cabinet_id, user=user)
    return {"insights": tips}


@router.get("/referral")
def my_referral(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Code de parrainage du cabinet + règles + stats."""
    if user.role == UserRole.ADMIN_WEBVOICE or not user.cabinet_id:
        return {"code": None, "available": False}
    from app.services import referral as referral_svc

    data = referral_svc.get_referral_overview(db, user.cabinet_id)
    data["available"] = True
    db.commit()
    return data


@router.post("/payment-failed", response_model=MessageResponse)
def simulate_payment_failed(
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
    cabinet_id: str | None = None,
):
    """Webhook démo — réservé admin plateforme (pas exposé aux cabinets clients)."""
    from app.services.retention_lifecycle import mark_payment_failed

    raise HTTPException(
        status_code=403,
        detail="Réservé au webhook paiement / admin plateforme — non disponible côté client.",
    )


@router.get("/history")
def billing_history(
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    events = billing_svc.list_events(db, user.cabinet_id)
    from app.models import BillingInvoice

    invoices = (
        db.query(BillingInvoice)
        .filter(BillingInvoice.cabinet_id == user.cabinet_id)
        .order_by(BillingInvoice.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "plan_slug": e.plan_slug,
                "detail": e.detail,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "invoices": [
            {
                "id": i.id,
                "number": i.number,
                "plan_name": i.plan_name,
                "amount_mad": i.amount_mad,
                "status": i.status,
                "billing_cycle": i.billing_cycle,
                "issued_at": i.issued_at.isoformat() if i.issued_at else (
                    i.created_at.isoformat() if i.created_at else None
                ),
                "kind": (
                    "trial_receipt"
                    if int(i.amount_mad or 0) == 0
                    or "trial" in (i.status or "").lower()
                    or "essai" in (i.status or "").lower()
                    else "invoice"
                ),
            }
            for i in invoices
        ],
    }


class SelectPlanResponse(BaseModel):
    message: str
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_html: Optional[str] = None


@router.post("/select-plan", response_model=SelectPlanResponse)
def select_plan_mock(
    data: SelectPlanRequest,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    """Choix de plan : Découverte immédiat ; plans payants = essai 30 j après carte."""
    plan = billing_svc.get_plan_by_slug(db, data.plan_slug)
    if plan and plan.slug == "enterprise":
        raise HTTPException(
            status_code=400,
            detail="L’essai Entreprise se fait après une demande commerciale (formulaire). Solo et Cabinet restent en libre-service.",
        )
    is_paid = bool(plan and (int(plan.price_mad_monthly or 0) > 0))

    if is_paid:
        digits = "".join(c for c in (data.card_number or "") if c.isdigit())
        if len(digits) < 13 or not (data.card_name or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Carte requise pour démarrer l'essai (nom + numéro valide).",
            )
        # Luhn light
        def _luhn(num: str) -> bool:
            s, alt = 0, False
            for ch in reversed(num):
                n = int(ch)
                if alt:
                    n *= 2
                    if n > 9:
                        n -= 9
                s += n
                alt = not alt
            return s % 10 == 0

        if not _luhn(digits):
            raise HTTPException(status_code=400, detail="Numéro de carte invalide.")
        last4 = digits[-4:]
        sub = billing_svc.start_paid_trial(
            db,
            user.cabinet_id,
            data.plan_slug,
            billing_cycle=data.billing_cycle,
            card_last4=last4,
        )
        days = int(plan.trial_days or 30) if plan else 30
        log_audit(
            db,
            "billing.paid_trial_started",
            user=user,
            request=request,
            details=f"{data.plan_slug}:{data.billing_cycle}:****{last4}",
        )
        from app.models import Cabinet

        cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
        inv = billing_svc.generate_trial_confirmation_invoice(
            db,
            user.cabinet_id,
            cabinet_name=cab.name if cab else "Cabinet",
            plan=plan,
            billing_cycle=data.billing_cycle,
            card_last4=last4,
            trial_days=days,
            cardholder_name=(data.card_name or "").strip(),
        )
        db.commit()
        try:
            from app.services.email import send_welcome_trial_email

            send_welcome_trial_email(
                user.email,
                full_name=user.full_name,
                cabinet_name=cab.name if cab else "Cabinet",
                trial_days=days,
            )
        except Exception:
            pass
        try:
            from app.services.email import send_payment_receipt_email

            send_payment_receipt_email(
                user.email,
                full_name=user.full_name,
                cabinet_name=cab.name if cab else "Cabinet",
                invoice_number=inv.number,
                amount_mad=int(inv.amount_mad or 0),
                plan_name=plan.name if plan else data.plan_slug,
                paid=False,
            )
        except Exception:
            pass
        return SelectPlanResponse(
            message=(
                f"Essai {days} jours démarré. Sans résiliation avant la fin, "
                "le plan sera facturé automatiquement (carte enregistrée)."
            ),
            invoice_id=inv.id,
            invoice_number=inv.number,
            invoice_html=inv.pdf_html,
        )

    sub = billing_svc.select_plan_mock(
        db, user.cabinet_id, data.plan_slug, billing_cycle=data.billing_cycle
    )
    log_audit(
        db,
        "billing.select_plan",
        user=user,
        request=request,
        details=f"{data.plan_slug}:{data.billing_cycle}",
    )
    db.commit()
    return SelectPlanResponse(message="Plan Découverte activé.")


@router.post("/cancel", response_model=MessageResponse)
def cancel_subscription(
    data: CancelSubscriptionRequest,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    billing_svc.request_cancellation(
        db,
        user.cabinet_id,
        reason_code=data.reason_code,
        reason_text=data.reason_text,
        user_id=user.id,
    )
    log_audit(db, "billing.cancel_requested", user=user, request=request, details=data.reason_code)
    db.commit()
    try:
        from app.models import Cabinet
        from app.services.billing import CANCEL_REASON_CODES
        from app.services.email import send_cancel_requested_email

        cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
        label = dict(CANCEL_REASON_CODES).get(data.reason_code, data.reason_code)
        send_cancel_requested_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cab.name if cab else "Cabinet",
            reason_label=label,
        )
    except Exception:
        pass
    return MessageResponse(
        message="Demande de résiliation enregistrée. Votre accès reste actif jusqu'à la fin de la période."
    )


@router.post("/cancel/undo", response_model=MessageResponse)
def undo_cancel(
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    billing_svc.undo_cancellation(db, user.cabinet_id, user_id=user.id)
    log_audit(db, "billing.cancel_undone", user=user, request=request)
    db.commit()
    try:
        from app.models import Cabinet
        from app.services.email import send_cancel_undone_email

        cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
        send_cancel_undone_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cab.name if cab else "Cabinet",
        )
    except Exception:
        pass
    return MessageResponse(message="Résiliation annulée. Votre abonnement se poursuit.")




@router.post("/payment-reminder", response_model=MessageResponse)
def payment_reminder(
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    """Relance e-mail : paiement échoué ou renouvellement proche."""
    from app.models import Cabinet
    from app.services.retention_lifecycle import mark_payment_failed, _admin_of_cabinet
    from app.services.email import send_renewal_reminder_email, send_payment_failed_email

    ent = billing_svc.get_entitlements(db, user.cabinet_id)
    cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    admin = user
    plan_name = ent.plan.name
    if ent.status == "past_due":
        # Force resend (bypass daily dedupe by calling email directly)
        ok = send_payment_failed_email(
            admin.email,
            full_name=admin.full_name,
            cabinet_name=cab.name if cab else "Cabinet",
            plan_name=plan_name,
            amount_mad=ent.plan.price_mad_monthly,
        )
        log_audit(db, "billing.payment_reminder", user=user, request=request, details="past_due")
        db.commit()
        return MessageResponse(
            message="E-mail de régularisation envoyé." if ok else "Échec d'envoi e-mail."
        )
    amount = (
        ent.plan.price_mad_yearly
        if str(ent.subscription.billing_cycle).endswith("yearly")
        or getattr(ent.subscription.billing_cycle, "value", "") == "yearly"
        else ent.plan.price_mad_monthly
    )
    end = ent.period_end
    label = end.strftime("%d/%m/%Y") if end else "—"
    days = 7
    if end:
        from datetime import timezone as tz

        e = end if end.tzinfo else end.replace(tzinfo=tz.utc)
        days = max(0, (e - billing_svc._now()).days)
    ok = send_renewal_reminder_email(
        admin.email,
        full_name=admin.full_name,
        cabinet_name=cab.name if cab else "Cabinet",
        plan_name=plan_name,
        days_left=days,
        amount_mad=amount,
        period_end_label=label,
    )
    log_audit(db, "billing.payment_reminder", user=user, request=request, details="renewal")
    db.commit()
    return MessageResponse(
        message="Rappel de renouvellement envoyé." if ok else "Échec d'envoi e-mail."
    )

@router.post("/invoices/generate")
def generate_invoice(
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    from app.models import Cabinet

    cab = db.query(Cabinet).filter(Cabinet.id == user.cabinet_id).first()
    inv = billing_svc.generate_invoice(
        db,
        user.cabinet_id,
        cabinet_name=cab.name if cab else "Cabinet",
        city=cab.city if cab else "",
        address=cab.address if cab else "",
    )
    log_audit(db, "billing.invoice_generate", user=user, request=request, details=inv.number)
    db.commit()
    try:
        from app.services.email import send_payment_receipt_email

        send_payment_receipt_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cab.name if cab else "Cabinet",
            invoice_number=inv.number,
            amount_mad=int(inv.amount_mad or 0),
            plan_name=inv.plan_name or "",
            paid=False,
        )
    except Exception:
        pass
    return {
        "id": inv.id,
        "number": inv.number,
        "amount_mad": inv.amount_mad,
        "html": inv.pdf_html,
    }


@router.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models import BillingInvoice

    inv = db.query(BillingInvoice).filter(BillingInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    if user.role == UserRole.ADMIN_WEBVOICE:
        pass
    elif user.role != UserRole.ADMIN_CABINET or inv.cabinet_id != user.cabinet_id:
        raise HTTPException(
            status_code=403,
            detail="Seul le responsable du cabinet peut consulter les factures.",
        )
    return {
        "id": inv.id,
        "number": inv.number,
        "plan_name": inv.plan_name,
        "amount_mad": inv.amount_mad,
        "status": inv.status,
        "html": inv.pdf_html,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "kind": (
            "trial_receipt"
            if int(inv.amount_mad or 0) == 0
            or "trial" in (inv.status or "").lower()
            or "essai" in (inv.status or "").lower()
            else "invoice"
        ),
    }


@router.get("/invoices/{invoice_id}/download")
def download_invoice_html(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Téléchargement HTML imprimable (Enregistrer en PDF via le navigateur)."""
    from fastapi.responses import HTMLResponse
    from app.models import BillingInvoice

    inv = db.query(BillingInvoice).filter(BillingInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    if user.role == UserRole.ADMIN_WEBVOICE:
        pass
    elif user.role != UserRole.ADMIN_CABINET or inv.cabinet_id != user.cabinet_id:
        raise HTTPException(
            status_code=403,
            detail="Seul le responsable du cabinet peut télécharger les factures.",
        )
    html = inv.pdf_html or f"<html><body><p>Facture {inv.number} — contenu indisponible.</p></body></html>"
    filename = f"LexHub-{inv.number}.html".replace("/", "-")
    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/cle-de-barre")
def api_cle_de_barre(
    data: CleDeBarreRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    from app.core.rate_limit import check_rate_limit
    from app.services.billing import begin_ai_action, finish_ai_action

    check_rate_limit(request, key="billing.cle", limit=6, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "cle_de_barre", request=request)
    try:
        result = generate_cle_de_barre(
            db,
            cabinet_id=user.cabinet_id,
            case_id=data.case_id,
            extra_instructions=data.extra_instructions,
            skip_spend=True,
        )
        log_audit(
            db,
            "billing.cle_de_barre",
            user=user,
            request=request,
            details=data.case_id,
        )
        finish_ai_action(db, user.cabinet_id, "cle_de_barre", slot_token=slot, success=True)
        db.commit()
        return result
    except Exception:
        finish_ai_action(db, user.cabinet_id, "cle_de_barre", slot_token=slot, success=False)
        db.rollback()
        raise


# ─── Admin WebVoice ───────────────────────────────────────────────

admin_router = APIRouter(prefix="/api/admin/billing", tags=["admin-billing"])


@admin_router.get("/cancel-insights")
def admin_cancel_insights(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    return billing_svc.analyze_cancel_reasons(db)


@admin_router.get("/plans", response_model=list[PlanOut])
def admin_list_plans(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    billing_svc.ensure_default_plans(db)
    db.commit()
    rows = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order.asc()).all()
    return [PlanOut(**billing_svc.plan_to_dict(p)) for p in rows]

@admin_router.patch("/plans/{plan_id}", response_model=PlanOut)
def admin_update_plan(
    plan_id: str,
    data: AdminPlanUpdate,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    payload = data.model_dump(exclude_unset=True)
    feats = payload.pop("features", None)
    for k, v in payload.items():
        setattr(plan, k, v)
    if feats is not None:
        plan.features_json = json.dumps(feats, ensure_ascii=False)
    plan.updated_at = datetime.now(timezone.utc)
    log_audit(db, "admin.plan.update", user=user, request=request, details=plan.slug)
    db.commit()
    db.refresh(plan)
    return PlanOut(**billing_svc.plan_to_dict(plan))


@admin_router.post("/cabinets/{cabinet_id}/assign", response_model=MessageResponse)
def admin_assign_plan(
    cabinet_id: str,
    data: AdminAssignPlanRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    from app.models import Cabinet, SubscriptionStatus, BillingCycle

    cab = db.query(Cabinet).filter(Cabinet.id == cabinet_id).first()
    if not cab:
        raise HTTPException(status_code=404, detail="Cabinet introuvable")
    plan = billing_svc.get_plan_by_slug(db, data.plan_slug)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    sub = billing_svc.ensure_subscription(db, cabinet_id)
    sub.plan_id = plan.id
    try:
        sub.status = SubscriptionStatus(data.status)
    except ValueError:
        sub.status = SubscriptionStatus.ACTIVE
    sub.billing_cycle = (
        BillingCycle.YEARLY if data.billing_cycle == "yearly" else BillingCycle.MONTHLY
    )
    if data.notes:
        sub.notes = data.notes
    sub.payment_provider = "manual"
    log_audit(
        db,
        "admin.plan.assign",
        user=user,
        request=request,
        details=f"{cabinet_id}:{data.plan_slug}",
    )
    db.commit()
    return MessageResponse(message=f"Plan {plan.name} assigné au cabinet {cab.name}")


@admin_router.get("/commercial-leads")
def admin_list_commercial_leads(
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CommercialLead)
        .order_by(CommercialLead.created_at.desc())
        .limit(300)
        .all()
    )
    return [
        {
            "id": r.id,
            "kind": r.kind,
            "full_name": r.full_name,
            "email": r.email,
            "phone": r.phone,
            "cabinet_name": r.cabinet_name,
            "city": r.city,
            "lawyers_count": r.lawyers_count,
            "message": r.message,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


class CommercialLeadStatusIn(BaseModel):
    status: Literal["new", "contacted", "qualified", "closed"]


@admin_router.patch("/commercial-leads/{lead_id}")
def admin_update_commercial_lead(
    lead_id: str,
    data: CommercialLeadStatusIn,
    request: Request,
    user: User = Depends(require_roles(UserRole.ADMIN_WEBVOICE)),
    db: Session = Depends(get_db),
):
    lead = db.query(CommercialLead).filter(CommercialLead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    lead.status = data.status
    log_audit(
        db,
        "billing.commercial_lead.status",
        user=user,
        request=request,
        details=f"{lead_id}:{data.status}",
    )
    db.commit()
    return {"ok": True, "id": lead.id, "status": lead.status}

# Appended by 031 — paiement Maroc (virement ICE + stubs CMI)

def _bank_payload() -> dict:
    return {
        "bank_rib": settings.LEXHUB_BANK_RIB or None,
        "bank_name": settings.LEXHUB_BANK_NAME or None,
        "beneficiary": settings.LEXHUB_BANK_BENEFICIARY or None,
        "ice": settings.LEXHUB_COMPANY_ICE or None,
        "cmi_ready": bool(settings.CMI_ENABLED or settings.CMI_MERCHANT_ID),
        "payzone_ready": bool(settings.PAYZONE_ENABLED or settings.PAYZONE_MERCHANT_ID),
        "card_status": (
            "env_ready"
            if (settings.CMI_ENABLED or settings.CMI_MERCHANT_ID)
            else "pending_operator"
        ),
        "note": (
            "Virement ICE disponible immédiatement. "
            "CMI / PayZone : environnement technique prêt — activation opérateur requise."
        ),
        "note_ar": (
            "التحويل البنكي مع ICE متاح فوراً. "
            "CMI / PayZone: البيئة التقنية جاهزة — يلزم تفعيل المشغّل."
        ),
    }


@router.get("/payment-env")
def payment_env(user: User = Depends(get_current_user)):
    return _bank_payload()


@router.post("/transfer-request", response_model=PaymentTransferResponse)
def create_transfer_request(
    data: PaymentTransferCreate,
    request: Request,
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    plan = billing_svc.get_plan_by_slug(db, data.plan_slug)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    amount = int(
        plan.price_mad_yearly if data.billing_cycle == "yearly" else plan.price_mad_monthly
    )
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Ce plan ne nécessite pas de virement")
    stamp = datetime.now(timezone.utc).strftime("%y%m%d")
    ref = f"LH-{stamp}-{user.cabinet_id[:6].upper()}-{data.plan_slug[:8].upper()}"
    row = PaymentTransferRequest(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        plan_slug=data.plan_slug,
        billing_cycle=data.billing_cycle,
        amount_mad=amount,
        reference=ref,
        status="pending",
        ice=settings.LEXHUB_COMPANY_ICE or None,
        notes=data.notes,
    )
    db.add(row)
    log_audit(db, "billing.transfer_request", user=user, request=request, details=ref)
    db.commit()
    db.refresh(row)
    bank = _bank_payload()
    rib = bank.get("bank_rib") or "(RIB à renseigner — LEXHUB_BANK_RIB)"
    ice = bank.get("ice") or "(ICE à renseigner — LEXHUB_COMPANY_ICE)"
    ben = bank.get("beneficiary") or "WEBVOICE SARL"
    bname = bank.get("bank_name") or "banque LexHub"
    instructions = (
        f"1) Effectuez un virement de {amount} MAD vers {ben} ({bname}).\n"
        f"2) RIB : {rib}\n"
        f"3) ICE : {ice}\n"
        f"4) Motif / référence OBLIGATOIRE : {ref}\n"
        f"5) Envoyez le justificatif à facturation@lexhub.space — activation sous 24–48 h ouvrés."
    )
    return PaymentTransferResponse(
        id=row.id,
        reference=row.reference,
        amount_mad=row.amount_mad,
        plan_slug=row.plan_slug,
        billing_cycle=row.billing_cycle,
        status=row.status,
        ice=row.ice,
        bank_rib=bank.get("bank_rib"),
        bank_name=bank.get("bank_name"),
        beneficiary=bank.get("beneficiary"),
        instructions=instructions,
        created_at=row.created_at,
    )


@router.get("/transfer-requests", response_model=list[PaymentTransferResponse])
def list_transfer_requests(
    user: User = Depends(require_cabinet_billing_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PaymentTransferRequest)
        .filter(PaymentTransferRequest.cabinet_id == user.cabinet_id)
        .order_by(PaymentTransferRequest.created_at.desc())
        .limit(50)
        .all()
    )
    bank = _bank_payload()
    out: list[PaymentTransferResponse] = []
    for row in rows:
        out.append(
            PaymentTransferResponse(
                id=row.id,
                reference=row.reference,
                amount_mad=row.amount_mad,
                plan_slug=row.plan_slug,
                billing_cycle=row.billing_cycle,
                status=row.status,
                ice=row.ice or bank.get("ice"),
                bank_rib=bank.get("bank_rib"),
                bank_name=bank.get("bank_name"),
                beneficiary=bank.get("beneficiary"),
                instructions=f"Référence {row.reference} — {row.amount_mad} MAD",
                created_at=row.created_at,
            )
        )
    return out


@router.post("/cmi/webhook")
async def cmi_webhook_stub(request: Request):
    """Stub webhook CMI — actif dès merchant ID fourni."""
    return {"ok": True, "provider": "cmi", "status": "accepted_stub"}


@router.post("/payzone/webhook")
async def payzone_webhook_stub(request: Request):
    """Stub webhook PayZone."""
    return {"ok": True, "provider": "payzone", "status": "accepted_stub"}

