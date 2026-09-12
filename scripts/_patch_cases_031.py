"""Patch cases.py for judicial fields + appeal deadline."""
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\api\cases.py")
t = p.read_text(encoding="utf-8")

if "court_file_number" not in t:
    t = t.replace(
        "from app.services.language import get_disclaimer, normalize_locale",
        "from app.services.language import get_disclaimer, normalize_locale\n"
        "from app.services.case_judicial import compute_appeal_deadline, default_appeal_days",
        1,
    )
    old_resp = """        opposing_quality=getattr(case, "opposing_quality", None),
        opposing_domicile=getattr(case, "opposing_domicile", None),
    )"""
    new_resp = """        opposing_quality=getattr(case, "opposing_quality", None),
        opposing_domicile=getattr(case, "opposing_domicile", None),
        court_file_number=getattr(case, "court_file_number", None),
        judge_name=getattr(case, "judge_name", None),
        chamber=getattr(case, "chamber", None),
        greffe=getattr(case, "greffe", None),
        procedure_status=getattr(case, "procedure_status", None),
        assistant_id=getattr(case, "assistant_id", None),
        last_decision_type=getattr(case, "last_decision_type", None),
        last_decision_date=getattr(case, "last_decision_date", None),
        notification_date=getattr(case, "notification_date", None),
        appeal_deadline_at=getattr(case, "appeal_deadline_at", None),
        appeal_deadline_days=getattr(case, "appeal_deadline_days", None),
    )"""
    t = t.replace(old_resp, new_resp, 1)

    # create case — add fields after opposing_domicile=
    t = t.replace(
        "        opposing_domicile=data.opposing_domicile,\n    )",
        """        opposing_domicile=data.opposing_domicile,
        court_file_number=getattr(data, "court_file_number", None),
        judge_name=getattr(data, "judge_name", None),
        chamber=getattr(data, "chamber", None),
        greffe=getattr(data, "greffe", None),
        procedure_status=getattr(data, "procedure_status", None) or "ouverture",
        assistant_id=getattr(data, "assistant_id", None),
        last_decision_type=getattr(data, "last_decision_type", None),
        last_decision_date=getattr(data, "last_decision_date", None),
        notification_date=getattr(data, "notification_date", None),
        appeal_deadline_days=getattr(data, "appeal_deadline_days", None),
        appeal_deadline_at=compute_appeal_deadline(
            getattr(data, "notification_date", None),
            getattr(data, "appeal_deadline_days", None),
            getattr(data, "jurisdiction_degree", None),
        ),
    )""",
        1,
    )

    # update: after model_dump, recompute deadline
    t = t.replace(
        """    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "tags" and value is not None:
            setattr(case, field, ",".join(value))
        elif value is not None:
            setattr(case, field, value)

    case.updated_at = datetime.now(timezone.utc)""",
        """    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "tags" and value is not None:
            setattr(case, field, ",".join(value))
        elif value is not None:
            setattr(case, field, value)

    # Recalcule délai de recours si notification / jours changés
    payload = data.model_dump(exclude_unset=True)
    if "notification_date" in payload or "appeal_deadline_days" in payload or "jurisdiction_degree" in payload:
        days = case.appeal_deadline_days or default_appeal_days(case.jurisdiction_degree)
        case.appeal_deadline_days = days
        case.appeal_deadline_at = compute_appeal_deadline(
            case.notification_date, days, case.jurisdiction_degree
        )

    case.updated_at = datetime.now(timezone.utc)""",
        1,
    )

tmp = p.with_suffix(".py.tmp")
tmp.write_text(t, encoding="utf-8")
try:
    tmp.replace(p)
except Exception:
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
print("cases api", "court_file_number" in t)
