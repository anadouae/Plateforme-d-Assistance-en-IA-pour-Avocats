from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\api\auth.py")
t = p.read_text(encoding="utf-8")
old = """    from app.core.config import settings as app_settings
    from app.services.billing import start_trial_for_cabinet

    start_trial_for_cabinet(
        db, cabinet.id, days=int(getattr(app_settings, "BILLING_TRIAL_DAYS", 14) or 14)
    )

    log_audit(db, "cabinet.register", user=user, request=request, details=cabinet.name)
    trial_days = int(getattr(app_settings, "BILLING_TRIAL_DAYS", 14) or 14)
    db.commit()

    try:
        from app.services.email import send_welcome_trial_email

        send_welcome_trial_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cabinet.name,
            trial_days=trial_days,
        )
    except Exception:
        pass

    return MessageResponse(
        message=(
            "Inscription réussie. Votre cabinet est actif — vous pouvez vous connecter."
        )
    )"""
new = """    from app.services.billing import start_free_for_cabinet

    start_free_for_cabinet(db, cabinet.id)

    log_audit(db, "cabinet.register", user=user, request=request, details=cabinet.name)
    db.commit()

    try:
        from app.services.email import send_welcome_free_email

        send_welcome_free_email(
            user.email,
            full_name=user.full_name,
            cabinet_name=cabinet.name,
        )
    except Exception:
        pass

    return MessageResponse(
        message=(
            "Inscription réussie. Votre cabinet est sur le plan Découverte (gratuit). "
            "Connectez-vous, puis upgradez depuis Tarifs si besoin."
        )
    )"""
if old not in t:
    raise SystemExit("pattern not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("ok")
