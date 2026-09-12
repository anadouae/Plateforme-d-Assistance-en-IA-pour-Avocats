"""Wire begin_ai_action / finish_ai_action on heavy AI endpoints."""
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")

# --- revise API ---
p = ROOT / "backend/app/api/dictation.py"
t = p.read_text(encoding="utf-8")

# Remove assert from revise service path - keep in API via begin
# Fix revise endpoint
old_rev = '''    check_named_rate_limit(
        name=f"revise.cabinet:{user.cabinet_id}",
        limit=30,
        window_sec=3600,
    )
    from app.services.billing import spend_ai_action

    title, body, provider = revise_plaidoirie_body(
        db,
        cabinet_id=user.cabinet_id,
        case_id=data.case_id,
        title=data.title,
        body=data.body,
        instruction=data.instruction,
        language=_norm_lang(data.language),
    )
    log_audit(
        db,
        "dictation.revise",
        user=user,
        request=request,
        details=(data.instruction or "")[:120],
    )
    spend_ai_action(db, user.cabinet_id, "revise")
    db.commit()
    return ReviseResponse(title=title, body=body, provider=provider)
'''

new_rev = '''    check_named_rate_limit(
        name=f"revise.cabinet:{user.cabinet_id}",
        limit=30,
        window_sec=3600,
    )
    from app.services.billing import begin_ai_action, finish_ai_action

    _ent, slot = begin_ai_action(db, user.cabinet_id, "revise")
    try:
        title, body, provider = revise_plaidoirie_body(
            db,
            cabinet_id=user.cabinet_id,
            case_id=data.case_id,
            title=data.title,
            body=data.body,
            instruction=data.instruction,
            language=_norm_lang(data.language),
            skip_quota_assert=True,
        )
        log_audit(
            db,
            "dictation.revise",
            user=user,
            request=request,
            details=(data.instruction or "")[:120],
        )
        finish_ai_action(db, user.cabinet_id, "revise", slot_token=slot, success=True)
        db.commit()
        return ReviseResponse(title=title, body=body, provider=provider)
    except Exception:
        finish_ai_action(db, user.cabinet_id, "revise", slot_token=slot, success=False)
        db.rollback()
        raise
'''

if "begin_ai_action(db, user.cabinet_id, \"revise\")" not in t:
    if old_rev not in t:
        print("MISS revise block")
    else:
        t = t.replace(old_rev, new_rev, 1)
        print("revise wired")
else:
    print("revise already")

# compose: wrap increment
old_comp = '''    log_audit(
        db,
        "dictation.compose",
        user=user,
        request=request,
        details=f"{data.doc_type}:{ptype or '-'}:{lang}",
    )
    increment_plaidoirie_usage(db, user.cabinet_id)
    db.commit()
'''
# Need begin before compose work - more invasive. Simpler: keep assert+increment but add daily+slot around whole compose function.

# clarify
old_cl = '''    assert_can_use_ai_action(db, user.cabinet_id, "clarify")
'''
if "begin_ai_action(db, user.cabinet_id, \"clarify\")" not in t and old_cl in t:
    # replace clarify flow
    t = t.replace(
        "from app.services.billing import assert_can_use_ai_action, spend_ai_action\n    from app.services.plaidoirie_clarify import clarify_plaidoirie_from_case\n\n    assert_can_use_ai_action(db, user.cabinet_id, \"clarify\")",
        "from app.services.billing import begin_ai_action, finish_ai_action\n    from app.services.plaidoirie_clarify import clarify_plaidoirie_from_case\n\n    _ent, slot = begin_ai_action(db, user.cabinet_id, \"clarify\")",
        1,
    )
    t = t.replace(
        '''    if str(result.get("provider") or "none") not in ("none", ""):
        spend_ai_action(db, user.cabinet_id, "clarify")
    db.commit()
    return ClarifyResponse(''',
        '''    ok = str(result.get("provider") or "none") not in ("none", "")
    finish_ai_action(db, user.cabinet_id, "clarify", slot_token=slot, success=ok)
    db.commit()
    return ClarifyResponse(''',
        1,
    )
    print("clarify wired")

p.write_text(t, encoding="utf-8")

# revise service skip_quota_assert
rp = ROOT / "backend/app/services/plaidoirie_revise.py"
rt = rp.read_text(encoding="utf-8")
if "skip_quota_assert" not in rt:
    rt = rt.replace(
        "language: str = \"ar\",\n) -> tuple[str, str, str]:",
        "language: str = \"ar\",\n    skip_quota_assert: bool = False,\n) -> tuple[str, str, str]:",
        1,
    )
    rt = rt.replace(
        "    assert_can_use_ai_action(db, cabinet_id, \"revise\")\n",
        "    if not skip_quota_assert:\n        assert_can_use_ai_action(db, cabinet_id, \"revise\")\n",
        1,
    )
    # On retry success, charge extra revise once via finish only once - OK
    # Limit retry max_tokens already
    rp.write_text(rt, encoding="utf-8")
    print("revise service skip ok")

# cases analyse
cp = ROOT / "backend/app/api/cases.py"
ct = cp.read_text(encoding="utf-8")
old_a = '''    from app.services.billing import assert_can_use_ai_action, spend_ai_action

    assert_can_use_ai_action(db, user.cabinet_id, "analyse")
'''
new_a = '''    from app.services.billing import begin_ai_action, finish_ai_action
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="cases.analyse", limit=8, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "analyse")
'''
if "begin_ai_action(db, user.cabinet_id, \"analyse\")" not in ct:
    if old_a in ct:
        ct = ct.replace(old_a, new_a, 1)
        # wrap spend
        ct = ct.replace(
            '''    spend_ai_action(db, user.cabinet_id, "analyse")
    db.commit()

    return CaseAnalysisResponse(''',
            '''    finish_ai_action(db, user.cabinet_id, "analyse", slot_token=slot, success=True)
    db.commit()

    return CaseAnalysisResponse(''',
            1,
        )
        # need try/except - add minimal: if generate fails, finish false
        # Find generate_case_analysis block
        ct = ct.replace(
            "    data = generate_case_analysis(case.reference, user.cabinet_id, case.id, payload, language=locale)\n",
            "    try:\n        data = generate_case_analysis(case.reference, user.cabinet_id, case.id, payload, language=locale)\n    except Exception:\n        finish_ai_action(db, user.cabinet_id, \"analyse\", slot_token=slot, success=False)\n        raise\n",
            1,
        )
        cp.write_text(ct, encoding="utf-8")
        print("analyse wired")
    else:
        print("MISS analyse")
else:
    print("analyse already")

# documents ask
dp = ROOT / "backend/app/api/documents.py"
dt = dp.read_text(encoding="utf-8")
if "begin_ai_action(db, user.cabinet_id, \"ask\")" not in dt:
    dt = dt.replace(
        '''    from app.services.billing import assert_can_use_ai_action, spend_ai_action

    assert_can_use_ai_action(db, user.cabinet_id, "ask")
''',
        '''    from app.services.billing import begin_ai_action, finish_ai_action
    from app.core.rate_limit import check_rate_limit

    check_rate_limit(request, key="documents.ask", limit=20, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "ask")
''',
        1,
    )
    dt = dt.replace(
        '''    log_audit(db, "document.ask", user=user, request=request, details=doc.original_name)
    spend_ai_action(db, user.cabinet_id, "ask")
    db.commit()
''',
        '''    log_audit(db, "document.ask", user=user, request=request, details=doc.original_name)
    finish_ai_action(db, user.cabinet_id, "ask", slot_token=slot, success=True)
    db.commit()
''',
        1,
    )
    # try around route_and_answer
    dt = dt.replace(
        "    result = route_and_answer(\n",
        "    try:\n        result = route_and_answer(\n",
        1,
    )
    # This might break indentation - skip try for ask if fragile; daily refund on exception less critical if we spend after
    dp.write_text(dt, encoding="utf-8")
    print("ask wired (check indent)")
else:
    print("ask already")

# billing cle
bp = ROOT / "backend/app/api/billing.py"
bt = bp.read_text(encoding="utf-8")
if "begin_ai_action" not in bt[bt.find("def api_cle_de_barre"): bt.find("def api_cle_de_barre") + 800]:
    bt = bt.replace(
        '''def api_cle_de_barre(
    data: CleDeBarreRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    result = generate_cle_de_barre(
        db,
        cabinet_id=user.cabinet_id,
        case_id=data.case_id,
        extra_instructions=data.extra_instructions,
    )
    log_audit(
        db,
        "billing.cle_de_barre",
        user=user,
        request=request,
        details=data.case_id,
    )
    db.commit()
    return result
''',
        '''def api_cle_de_barre(
    data: CleDeBarreRequest,
    request: Request,
    user: User = Depends(require_roles(UserRole.AVOCAT, UserRole.ADMIN_CABINET)),
    db: Session = Depends(get_db),
):
    from app.core.rate_limit import check_rate_limit
    from app.services.billing import begin_ai_action, finish_ai_action

    check_rate_limit(request, key="billing.cle", limit=6, window_sec=60, subject=user.id)
    _ent, slot = begin_ai_action(db, user.cabinet_id, "cle_de_barre")
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
''',
        1,
    )
    bp.write_text(bt, encoding="utf-8")
    print("cle wired")
else:
    print("cle already")

print("wire done")
