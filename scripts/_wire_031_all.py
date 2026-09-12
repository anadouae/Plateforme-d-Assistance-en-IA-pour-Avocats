# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance")


def wb(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".wtmp")
    tmp.write_text(text, encoding="utf-8")
    path.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)


# —— cases comments ——
import runpy
runpy.run_path(str(ROOT / "scripts/_patch_cases_comments.py"))

# —— billing ——
bp = ROOT / "backend/app/api/billing.py"
bt = bp.read_text(encoding="utf-8")
if "def create_transfer_request" not in bt:
    if "PaymentTransferRequest" not in bt:
        bt = bt.replace(
            "from app.models import SubscriptionPlan, User, UserRole",
            "from app.models import PaymentTransferRequest, SubscriptionPlan, User, UserRole",
            1,
        )
    if "PaymentTransferCreate" not in bt:
        bt = bt.replace(
            "from app.schemas import MessageResponse",
            "from app.schemas import MessageResponse, PaymentTransferCreate, PaymentTransferResponse",
            1,
        )
    if "from app.core.config import settings" not in bt:
        bt = bt.replace(
            "from app.core.database import get_db",
            "from app.core.config import settings\nfrom app.core.database import get_db",
            1,
        )
    append = (ROOT / "scripts/_billing_031_append.py").read_text(encoding="utf-8")
    # strip comment header lines that aren't valid mid-file? Keep as is - first lines are comments OK
    wb(bp, bt.rstrip() + "\n\n" + append + "\n")
    print("billing OK")
else:
    print("billing already")

# —— workspace ICS + assignee ——
wp = ROOT / "backend/app/api/workspace.py"
wt = wp.read_text(encoding="utf-8")
if "export_agenda_ics" not in wt:
    if "from fastapi.responses import Response" not in wt:
        wt = wt.replace(
            "from fastapi import APIRouter, Depends, HTTPException, Request, status\n",
            "from fastapi import APIRouter, Depends, HTTPException, Request, status\n"
            "from fastapi.responses import Response\n",
            1,
        )
    wt = wt.replace(
        "        status=task.status,\n        due_at=task.due_at,\n        created_at=task.created_at,\n        updated_at=task.updated_at,\n    )",
        "        status=task.status,\n        due_at=task.due_at,\n"
        "        assignee_id=getattr(task, \"assignee_id\", None),\n"
        "        assignee_name=(\n"
        "            db.query(User).filter(User.id == task.assignee_id).first().full_name\n"
        "            if getattr(task, \"assignee_id\", None)\n"
        "            else None\n"
        "        ),\n"
        "        created_at=task.created_at,\n        updated_at=task.updated_at,\n    )",
        1,
    )
    # fix assignee_name - that query is ugly if None. Better simpler:
    # Actually if assignee_id set but user deleted, .first() is None -> AttributeError
    # Fix after with safer helper - for now replace with safer version
    wt = wt.replace(
        "        assignee_id=getattr(task, \"assignee_id\", None),\n"
        "        assignee_name=(\n"
        "            db.query(User).filter(User.id == task.assignee_id).first().full_name\n"
        "            if getattr(task, \"assignee_id\", None)\n"
        "            else None\n"
        "        ),\n",
        "        assignee_id=getattr(task, \"assignee_id\", None),\n"
        "        assignee_name=_task_assignee_name(db, getattr(task, \"assignee_id\", None)),\n",
        1,
    )
    wt = wt.replace(
        "def _task_resp(db: Session, task: CaseTask) -> CaseTaskResponse:\n",
        "def _task_assignee_name(db: Session, assignee_id: str | None) -> str | None:\n"
        "    if not assignee_id:\n"
        "        return None\n"
        "    u = db.query(User).filter(User.id == assignee_id).first()\n"
        "    return u.full_name if u else None\n\n\n"
        "def _task_resp(db: Session, task: CaseTask) -> CaseTaskResponse:\n",
        1,
    )
    wt = wt.replace(
        "        status=data.status,\n        due_at=data.due_at,\n    )",
        "        status=data.status,\n        due_at=data.due_at,\n"
        "        assignee_id=getattr(data, \"assignee_id\", None),\n    )",
        1,
    )
    # update task assignee
    if "if data.due_at is not None:" in wt and "assignee_id" not in wt.split("def update_task")[1].split("def delete_task")[0]:
        # find update_task due_at assignment
        pass
    # ICS before delete agenda or after create
    ics = '''

@router.get("/agenda/export.ics")
def export_agenda_ics(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export ICS pour Google Calendar / Outlook."""
    q = db.query(AgendaEvent).filter(AgendaEvent.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(AgendaEvent.case_id == case_id)
    events = q.order_by(AgendaEvent.starts_at.asc()).limit(500).all()

    def _fmt(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LexHub//Agenda Cabinet//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for ev in events:
        desc = (ev.description or "").replace("\\\\n", " ").replace(",", "\\\\,")
        loc_parts = [p for p in [getattr(ev, "location", None), getattr(ev, "city", None)] if p]
        loc = " — ".join(loc_parts).replace(",", "\\\\,")
        title = (ev.title or "Événement").replace(",", "\\\\,")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ev.id}@lexhub.space",
                f"DTSTAMP:{_fmt(datetime.now(timezone.utc))}",
                f"DTSTART:{_fmt(ev.starts_at)}",
            ]
        )
        if ev.ends_at:
            lines.append(f"DTEND:{_fmt(ev.ends_at)}")
        lines.append(f"SUMMARY:{title}")
        if desc:
            lines.append(f"DESCRIPTION:{desc}")
        if loc:
            lines.append(f"LOCATION:{loc}")
        lines.append(f"CATEGORIES:{(ev.event_type or 'other').upper()}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    body = "\\r\\n".join(lines) + "\\r\\n"
    return Response(
        content=body.encode("utf-8"),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": \'attachment; filename="agenda-lexhub.ics"\'},
    )

'''
    # Fix ics string properly without escape mess - build with chr
    # Rewrite ICS append without escaped newlines in source file content
    ics_path = ROOT / "scripts/_ics_append.py"
    ics_path.write_text(
        '''
@router.get("/agenda/export.ics")
def export_agenda_ics(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export ICS pour Google Calendar / Outlook."""
    q = db.query(AgendaEvent).filter(AgendaEvent.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(AgendaEvent.case_id == case_id)
    events = q.order_by(AgendaEvent.starts_at.asc()).limit(500).all()

    def _fmt(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LexHub//Agenda Cabinet//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for ev in events:
        desc = (ev.description or "").replace("\\n", " ").replace(",", "\\\\,")
        loc_parts = [p for p in [getattr(ev, "location", None), getattr(ev, "city", None)] if p]
        loc = " — ".join(loc_parts).replace(",", "\\\\,")
        title = (ev.title or "Événement").replace(",", "\\\\,")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ev.id}@lexhub.space",
                f"DTSTAMP:{_fmt(datetime.now(timezone.utc))}",
                f"DTSTART:{_fmt(ev.starts_at)}",
            ]
        )
        if ev.ends_at:
            lines.append(f"DTEND:{_fmt(ev.ends_at)}")
        lines.append(f"SUMMARY:{title}")
        if desc:
            lines.append(f"DESCRIPTION:{desc}")
        if loc:
            lines.append(f"LOCATION:{loc}")
        lines.append(f"CATEGORIES:{(ev.event_type or 'other').upper()}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    body = "\\r\\n".join(lines) + "\\r\\n"
    return Response(
        content=body.encode("utf-8"),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="agenda-lexhub.ics"'},
    )
''',
        encoding="utf-8",
    )
    # The above still has escape issues. Write ICS function with explicit join.
    ics_code = r'''
@router.get("/agenda/export.ics")
def export_agenda_ics(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export ICS pour Google Calendar / Outlook."""
    q = db.query(AgendaEvent).filter(AgendaEvent.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(AgendaEvent.case_id == case_id)
    events = q.order_by(AgendaEvent.starts_at.asc()).limit(500).all()

    def _fmt(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LexHub//Agenda Cabinet//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for ev in events:
        desc = (ev.description or "").replace("\n", " ").replace(",", "\,")
        loc_parts = [p for p in [getattr(ev, "location", None), getattr(ev, "city", None)] if p]
        loc = " — ".join(loc_parts).replace(",", "\,")
        title = (ev.title or "Événement").replace(",", "\,")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{ev.id}@lexhub.space",
                f"DTSTAMP:{_fmt(datetime.now(timezone.utc))}",
                f"DTSTART:{_fmt(ev.starts_at)}",
            ]
        )
        if ev.ends_at:
            lines.append(f"DTEND:{_fmt(ev.ends_at)}")
        lines.append(f"SUMMARY:{title}")
        if desc:
            lines.append(f"DESCRIPTION:{desc}")
        if loc:
            lines.append(f"LOCATION:{loc}")
        lines.append(f"CATEGORIES:{(ev.event_type or 'other').upper()}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(
        content=body.encode("utf-8"),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="agenda-lexhub.ics"'},
    )
'''
    # Insert before delete_agenda_event
    marker = '@router.delete("/agenda/{event_id}", status_code=status.HTTP_204_NO_CONTENT)'
    if marker in wt:
        wt = wt.replace(marker, ics_code + "\n\n" + marker, 1)
    else:
        wt = wt.rstrip() + "\n" + ics_code + "\n"

    # patch update_task for assignee
    if "data.assignee_id" not in wt:
        wt = wt.replace(
            "    if data.due_at is not None:\n        task.due_at = data.due_at\n    task.updated_at = datetime.now(timezone.utc)",
            "    if data.due_at is not None:\n        task.due_at = data.due_at\n"
            "    if getattr(data, \"assignee_id\", None) is not None or (\n"
            "        hasattr(data, \"model_fields_set\") and \"assignee_id\" in getattr(data, \"model_fields_set\", set())\n"
            "    ):\n"
            "        task.assignee_id = data.assignee_id\n"
            "    elif \"assignee_id\" in data.model_dump(exclude_unset=True):\n"
            "        task.assignee_id = data.assignee_id\n"
            "    task.updated_at = datetime.now(timezone.utc)",
            1,
        )
        # simpler approach
        wt = wt.replace(
            "    elif \"assignee_id\" in data.model_dump(exclude_unset=True):\n"
            "        task.assignee_id = data.assignee_id\n"
            "    if getattr(data, \"assignee_id\", None) is not None or (\n"
            "        hasattr(data, \"model_fields_set\") and \"assignee_id\" in getattr(data, \"model_fields_set\", set())\n"
            "    ):\n"
            "        task.assignee_id = data.assignee_id\n",
            "    if \"assignee_id\" in data.model_dump(exclude_unset=True):\n"
            "        task.assignee_id = data.assignee_id\n",
            1,
        )

    wb(wp, wt)
    print("workspace OK")
else:
    print("workspace already")

print("ALL API wire step1 done")
