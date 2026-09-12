from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\celery_app.py")
t = p.read_text(encoding="utf-8")
old = """    beat_schedule={
        \"agenda-remind-48h-every-15min\": {
            \"task\": \"agenda_remind_48h\",
            \"schedule\": 900.0,  # 15 minutes
        },
        \"trial-lifecycle-hourly\": {
            \"task\": \"trial_lifecycle_hourly\",
            \"schedule\": 3600.0,  # 1 heure
        },
    },"""
new = """    beat_schedule={
        \"agenda-remind-48h-every-15min\": {
            \"task\": \"agenda_remind_48h\",
            \"schedule\": 900.0,  # 15 minutes
        },
        \"trial-lifecycle-hourly\": {
            \"task\": \"trial_lifecycle_hourly\",
            \"schedule\": 3600.0,  # 1 heure
        },
        \"retention-daily-9h\": {
            \"task\": \"retention_lifecycle_daily\",
            \"schedule\": crontab(hour=9, minute=0),  # 09:00 Africa/Casablanca
        },
        \"retention-weekly-digest\": {
            \"task\": \"retention_weekly_digest\",
            \"schedule\": crontab(hour=9, minute=30, day_of_week=1),  # lundi
        },
    },"""
if old not in t:
    raise SystemExit("beat block not found")
p.write_text(t.replace(old, new), encoding="utf-8")
print("celery_app ok")

tp = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\services\tasks.py")
tt = tp.read_text(encoding="utf-8")
extra = '''

@celery_app.task(name="retention_lifecycle_daily")
def retention_lifecycle_daily():
    """Renouvellement J-7/J-1, tips J+1/J+2, inactivité 14j, 2FA, changelog mensuel."""
    set_correlation_id("celery:retention_daily")
    db = SessionLocal()
    try:
        from app.services.retention_lifecycle import process_retention_daily

        result = process_retention_daily(db)
        logger.info("Retention daily: %s", result)
        return result
    except Exception as exc:
        logger.exception("retention_lifecycle_daily failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()


@celery_app.task(name="retention_weekly_digest")
def retention_weekly_digest():
    """Digest hebdomadaire activité cabinet (lundi)."""
    set_correlation_id("celery:retention_weekly")
    db = SessionLocal()
    try:
        from app.services.retention_lifecycle import process_weekly_digests

        result = process_weekly_digests(db)
        logger.info("Weekly digest: %s", result)
        return result
    except Exception as exc:
        logger.exception("retention_weekly_digest failed: %s", exc)
        return {"status": "failed", "reason": str(exc)[:200]}
    finally:
        db.close()
'''
if "retention_lifecycle_daily" not in tt:
    tp.write_text(tt.rstrip() + extra + "\n", encoding="utf-8")
    print("tasks ok")
else:
    print("tasks already has retention")
