from pathlib import Path

path = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\billing.py")
text = path.read_text(encoding="utf-8")

# Harden assert_can_use_ai_action + spend + add begin/finish helpers
old_assert = '''def assert_can_use_ai_action(db: Session, cabinet_id: str, action: str) -> Entitlements:
    """
    Gate unifié pour toute action IA ChatGPT.
    Vérifie : impayé, crédits pondérés, et plafond produit (revise/analyse/ask…).
    """
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    _assert_ai_credits(ent, action)
'''

new_assert = '''def assert_can_use_ai_action(db: Session, cabinet_id: str, action: str) -> Entitlements:
    """
    Gate unifié pour toute action IA ChatGPT.
    Vérifie : impayé, crédits mensuels, plafond journalier, produit, slots.
    """
    ent = get_entitlements(db, cabinet_id)
    _raise_if_restricted(ent)
    _assert_ai_credits(ent, action)
    cost = ai_credit_cost(action)
    from app.core.rate_limit import check_cabinet_ai_daily

    check_cabinet_ai_daily(cabinet_id, cost, ai_daily_cap_for(ent.plan.slug))
'''

if "check_cabinet_ai_daily" not in text[text.find("def assert_can_use_ai_action"): text.find("def assert_can_use_ai_action") + 800]:
    if old_assert not in text:
        raise SystemExit("assert block missing")
    text = text.replace(old_assert, new_assert, 1)
    print("assert patched")
else:
    print("assert already has daily")

old_spend = '''def spend_ai_action(db: Session, cabinet_id: str, action: str) -> None:
    """Incrémente crédits + compteurs produit après succès d'une action IA."""
    usage = get_or_create_usage(db, cabinet_id)
    cost = ai_credit_cost(action)
    usage.ai_credits_used = int(getattr(usage, "ai_credits_used", 0) or 0) + cost
'''

new_spend = '''def spend_ai_action(db: Session, cabinet_id: str, action: str) -> None:
    """Incrémente crédits + compteurs produit (verrou ligne) après / pendant action IA."""
    ym = _period_ym()
    usage = (
        db.query(UsageCounter)
        .filter(UsageCounter.cabinet_id == cabinet_id, UsageCounter.period_ym == ym)
        .with_for_update()
        .first()
    )
    if not usage:
        usage = get_or_create_usage(db, cabinet_id)
        usage = (
            db.query(UsageCounter)
            .filter(UsageCounter.id == usage.id)
            .with_for_update()
            .first()
        )
    cost = ai_credit_cost(action)
    # Re-check monthly under lock (anti race parallèle)
    ent = get_entitlements(db, cabinet_id)
    lim = ent.ai_credits_limit
    used = int(getattr(usage, "ai_credits_used", 0) or 0)
    if lim >= 0 and used + cost > lim:
        from app.core.rate_limit import refund_cabinet_ai_daily

        refund_cabinet_ai_daily(cabinet_id, cost)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Crédits IA du mois insuffisants ({used}/{lim}).",
        )
    usage.ai_credits_used = used + cost
'''

if "with_for_update()" not in text[text.find("def spend_ai_action"): text.find("def spend_ai_action") + 600]:
    if old_spend not in text:
        raise SystemExit("spend block missing")
    text = text.replace(old_spend, new_spend, 1)
    print("spend patched")
else:
    print("spend already locked")

helper = '''
def begin_ai_action(db: Session, cabinet_id: str, action: str) -> tuple[Entitlements, str | None]:
    """
    Prépare une action IA : quotas + daily + slot concurrent.
    Retourne (entitlements, slot_token). Toujours appeler finish_ai_action.
    """
    from app.core.rate_limit import acquire_cabinet_ai_slot

    ent = assert_can_use_ai_action(db, cabinet_id, action)
    token = acquire_cabinet_ai_slot(
        cabinet_id,
        ai_concurrent_slots_for(ent.plan.slug),
        ttl_sec=240 if action in HEAVY_AI_ACTIONS else 120,
    )
    return ent, token


def finish_ai_action(
    db: Session,
    cabinet_id: str,
    action: str,
    *,
    slot_token: str | None,
    success: bool,
) -> None:
    """Debite si succès ; libère le slot ; rembourse le daily si échec."""
    from app.core.rate_limit import release_cabinet_ai_slot, refund_cabinet_ai_daily

    try:
        if success:
            spend_ai_action(db, cabinet_id, action)
        else:
            refund_cabinet_ai_daily(cabinet_id, ai_credit_cost(action))
    finally:
        release_cabinet_ai_slot(cabinet_id, slot_token)


'''

if "def begin_ai_action" not in text:
    # insert before select_plan_mock
    anchor = "\ndef select_plan_mock("
    if anchor not in text:
        raise SystemExit("select_plan_mock missing")
    text = text.replace(anchor, helper + anchor, 1)
    print("begin/finish added")
else:
    print("begin already")

# Entitlements to_dict: expose daily caps
if '"ai_daily_limit"' not in text:
    text = text.replace(
        '"ai_credit_costs": dict(AI_ACTION_CREDITS),',
        '"ai_credit_costs": dict(AI_ACTION_CREDITS),\n'
        '            "ai_daily_limit": ai_daily_cap_for(self.plan.slug),\n'
        '            "ai_concurrent_slots": ai_concurrent_slots_for(self.plan.slug),',
        1,
    )
    print("entitlements daily fields")

path.write_text(text, encoding="utf-8")
print("billing harden done")
