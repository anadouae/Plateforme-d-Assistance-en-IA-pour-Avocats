# -*- coding: utf-8 -*-
"""Billing payment-env + transfer request endpoints."""
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\api\billing.py")
t = p.read_text(encoding="utf-8")

if "payment-env" in t and "transfer-request" in t:
    print("already")
else:
    # imports
    if "PaymentTransferRequest" not in t:
        t = t.replace(
            "from app.models import SubscriptionPlan, User, UserRole",
            "from app.models import PaymentTransferRequest, SubscriptionPlan, User, UserRole",
            1,
        )
    if "PaymentTransferCreate" not in t:
        t = t.replace(
            "from app.schemas import MessageResponse",
            "from app.schemas import MessageResponse, PaymentTransferCreate, PaymentTransferResponse",
            1,
        )
    if "from app.core.config import settings" not in t:
        t = t.replace(
            "from app.core.database import get_db",
            "from app.core.config import settings\nfrom app.core.database import get_db",
            1,
        )

    block = '''

def _bank_payload() -> dict:
    return {
        "bank_rib": settings.LEXHUB_BANK_RIB or None,
        "bank_name": settings.LEXHUB_BANK_NAME or None,
        "beneficiary": settings.LEXHUB_BANK_BENEFICIARY or None,
        "ice": settings.LEXHUB_COMPANY_ICE or None,
        "cmi_ready": bool(settings.CMI_ENABLED or settings.CMI_MERCHANT_ID),
        "payzone_ready": bool(settings.PAYZONE_ENABLED or settings.PAYZONE_MERCHANT_ID),
        "card_status": "env_ready" if (settings.CMI_ENABLED or settings.CMI_MERCHANT_ID) else "pending_operator",
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
    amount = int(plan.price_mad_yearly if data.billing_cycle == "yearly" else plan.price_mad_monthly)
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
    instructions = (
        f"1) Effectuez un virement de {amount} MAD vers {bank.get('beneficiary') or 'WEBVOICE SARL'} "
        f"({bank.get('bank_name') or 'banque LexHub'}).\\n"
        f"2) RIB : {rib}\\n"
        f"3) ICE : {ice}\\n"
        f"4) Motif / référence OBLIGATOIRE : {ref}\\n"
        f"5) Envoyez le justificatif à facturation@lexhub.space — activation sous 24–48 h ouvrés."
    ).replace("\\\\n", "\\n")
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
        instructions=instructions.replace("\\n", "\\n"),
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
    out = []
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
def cmi_webhook_stub(request: Request):
    """Stub webhook CMI — actif dès merchant ID fourni."""
    return {"ok": True, "provider": "cmi", "status": "accepted_stub"}


@router.post("/payzone/webhook")
def payzone_webhook_stub(request: Request):
    """Stub webhook PayZone."""
    return {"ok": True, "provider": "payzone", "status": "accepted_stub"}
'''
    # Fix instructions newlines properly in the block
    block = block.replace(
        'f"1) Effectuez un virement de {amount} MAD vers {bank.get(\'beneficiary\') or \'WEBVOICE SARL\'} '
        'f"({bank.get(\'bank_name\') or \'banque LexHub\'}).\\\\n"\n'
        '        f"2) RIB : {rib}\\\\n"\n'
        '        f"3) ICE : {ice}\\\\n"\n'
        '        f"4) Motif / référence OBLIGATOIRE : {ref}\\\\n"\n'
        '        f"5) Envoyez le justificatif à facturation@lexhub.space — activation sous 24–48 h ouvrés."\n'
        '    ).replace("\\\\\\\\n", "\\\\n")',
        'f"1) Effectuez un virement de {amount} MAD vers {bank.get(\'beneficiary\') or \'WEBVOICE SARL\'} "'
        '        f"({bank.get(\'bank_name\') or \'banque LexHub\'}).\\n"\n'
        '        f"2) RIB : {rib}\\n"\n'
        '        f"3) ICE : {ice}\\n"\n'
        '        f"4) Motif / référence OBLIGATOIRE : {ref}\\n"\n'
        '        f"5) Envoyez le justificatif à facturation@lexhub.space — activation sous 24–48 h ouvrés."\n'
        '    )',
    )
    # Simpler: rewrite create function instructions cleanly after insert
    t = t.rstrip() + "\n" + block + "\n"
    # Fix garbled instructions
    bad = ').replace("\\\\n", "\\n")'
    if bad in t:
        t = t.replace(bad, ")")
    t = t.replace('instructions=instructions.replace("\\n", "\\n"),', "instructions=instructions,")

    tmp = p.with_suffix(".py.wtmp")
    tmp.write_text(t, encoding="utf-8")
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
    print("billing patched")
