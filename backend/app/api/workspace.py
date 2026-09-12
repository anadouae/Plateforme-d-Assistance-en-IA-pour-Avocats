"""Notes, tâches et agenda cabinet — workspace léger type ClickUp juridique."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit
from app.core.database import get_db
from app.models import AgendaEvent, ActivityArchive, AuditLog, Case, CaseNote, CaseTask, Document, PlaidoirieDraft, User
from app.schemas import (
    ActivityArchiveItem,
    AgendaEventCreate,
    AgendaEventResponse,
    AgendaEventUpdate,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteUpdate,
    CaseTaskCreate,
    CaseTaskResponse,
    CaseTaskUpdate,
    WorkspaceActivityItem,
    WorkspaceSearchHit,
    WorkspaceSummaryResponse,
)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


def _case_ref(db: Session, case_id: str | None, cabinet_id: str) -> str | None:
    if not case_id:
        return None
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == cabinet_id)
        .first()
    )
    return case.reference if case else None


def _ensure_case(db: Session, case_id: str | None, cabinet_id: str) -> None:
    if not case_id:
        return
    exists = (
        db.query(Case.id)
        .filter(Case.id == case_id, Case.cabinet_id == cabinet_id)
        .first()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Dossier introuvable")


def _note_resp(db: Session, note: CaseNote) -> CaseNoteResponse:
    return CaseNoteResponse(
        id=note.id,
        title=note.title,
        body=note.body,
        case_id=note.case_id,
        case_reference=_case_ref(db, note.case_id, note.cabinet_id),
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _task_assignee_name(db: Session, assignee_id: str | None) -> str | None:
    if not assignee_id:
        return None
    u = db.query(User).filter(User.id == assignee_id).first()
    return u.full_name if u else None


def _task_resp(db: Session, task: CaseTask) -> CaseTaskResponse:
    return CaseTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        case_id=task.case_id,
        case_reference=_case_ref(db, task.case_id, task.cabinet_id),
        status=task.status,
        due_at=task.due_at,
        assignee_id=getattr(task, "assignee_id", None),
        assignee_name=_task_assignee_name(db, getattr(task, "assignee_id", None)),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _event_resp(db: Session, event: AgendaEvent) -> AgendaEventResponse:
    return AgendaEventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        case_id=event.case_id,
        case_reference=_case_ref(db, event.case_id, event.cabinet_id),
        event_type=event.event_type,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        meet_url=getattr(event, "meet_url", None),
        city=getattr(event, "city", None),
        location=getattr(event, "location", None),
        created_at=event.created_at,
    )


# ─── Summary (dashboard) ─────────────────────────────────────────────────────


@router.get("/summary", response_model=WorkspaceSummaryResponse)
def workspace_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=21)
    events = (
        db.query(AgendaEvent)
        .filter(
            AgendaEvent.cabinet_id == user.cabinet_id,
            AgendaEvent.starts_at >= now - timedelta(hours=6),
            AgendaEvent.starts_at <= horizon,
        )
        .order_by(AgendaEvent.starts_at.asc())
        .limit(8)
        .all()
    )
    tasks = (
        db.query(CaseTask)
        .filter(
            CaseTask.cabinet_id == user.cabinet_id,
            CaseTask.status != "done",
        )
        .order_by(CaseTask.due_at.asc().nullslast(), CaseTask.updated_at.desc())
        .limit(8)
        .all()
    )
    notes = (
        db.query(CaseNote)
        .filter(CaseNote.cabinet_id == user.cabinet_id)
        .order_by(CaseNote.updated_at.desc())
        .limit(5)
        .all()
    )
    return WorkspaceSummaryResponse(
        upcoming_events=[_event_resp(db, e) for e in events],
        open_tasks=[_task_resp(db, t) for t in tasks],
        recent_notes=[_note_resp(db, n) for n in notes],
    )


# ─── Notes ───────────────────────────────────────────────────────────────────


@router.get("/notes", response_model=list[CaseNoteResponse])
def list_notes(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(CaseNote).filter(CaseNote.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(CaseNote.case_id == case_id)
    notes = q.order_by(CaseNote.updated_at.desc()).limit(100).all()
    return [_note_resp(db, n) for n in notes]


@router.post("/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    data: CaseNoteCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_case(db, data.case_id, user.cabinet_id)
    note = CaseNote(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        case_id=data.case_id,
        title=data.title.strip(),
        body=data.body or "",
    )
    db.add(note)
    log_audit(db, "note.create", user=user, request=request, details=note.title)
    db.commit()
    db.refresh(note)
    return _note_resp(db, note)


@router.patch("/notes/{note_id}", response_model=CaseNoteResponse)
def update_note(
    note_id: str,
    data: CaseNoteUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = (
        db.query(CaseNote)
        .filter(CaseNote.id == note_id, CaseNote.cabinet_id == user.cabinet_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    if data.case_id is not None:
        _ensure_case(db, data.case_id or None, user.cabinet_id)
        note.case_id = data.case_id or None
    if data.title is not None:
        note.title = data.title.strip()
    if data.body is not None:
        note.body = data.body
    db.commit()
    db.refresh(note)
    return _note_resp(db, note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = (
        db.query(CaseNote)
        .filter(CaseNote.id == note_id, CaseNote.cabinet_id == user.cabinet_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    db.delete(note)
    db.commit()


# ─── Tasks ───────────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=list[CaseTaskResponse])
def list_tasks(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(CaseTask).filter(CaseTask.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(CaseTask.case_id == case_id)
    tasks = q.order_by(CaseTask.due_at.asc().nullslast(), CaseTask.updated_at.desc()).limit(100).all()
    return [_task_resp(db, t) for t in tasks]


@router.post("/tasks", response_model=CaseTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    data: CaseTaskCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_case(db, data.case_id, user.cabinet_id)
    task = CaseTask(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        case_id=data.case_id,
        title=data.title.strip(),
        description=data.description,
        status=data.status,
        due_at=data.due_at,
        assignee_id=getattr(data, "assignee_id", None),
    )
    db.add(task)
    log_audit(db, "task.create", user=user, request=request, details=task.title)
    db.commit()
    db.refresh(task)
    return _task_resp(db, task)


@router.patch("/tasks/{task_id}", response_model=CaseTaskResponse)
def update_task(
    task_id: str,
    data: CaseTaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(CaseTask)
        .filter(CaseTask.id == task_id, CaseTask.cabinet_id == user.cabinet_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if data.case_id is not None:
        _ensure_case(db, data.case_id or None, user.cabinet_id)
        task.case_id = data.case_id or None
    if data.title is not None:
        task.title = data.title.strip()
    if data.description is not None:
        task.description = data.description
    if data.status is not None:
        task.status = data.status
    if data.due_at is not None:
        task.due_at = data.due_at
    if "assignee_id" in data.model_dump(exclude_unset=True):
        task.assignee_id = data.assignee_id
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return _task_resp(db, task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = (
        db.query(CaseTask)
        .filter(CaseTask.id == task_id, CaseTask.cabinet_id == user.cabinet_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    db.delete(task)
    db.commit()


# ─── Agenda ──────────────────────────────────────────────────────────────────


@router.get("/agenda", response_model=list[AgendaEventResponse])
def list_agenda(
    case_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(AgendaEvent).filter(AgendaEvent.cabinet_id == user.cabinet_id)
    if case_id:
        q = q.filter(AgendaEvent.case_id == case_id)
    events = q.order_by(AgendaEvent.starts_at.asc()).limit(150).all()
    return [_event_resp(db, e) for e in events]


@router.post("/agenda", response_model=AgendaEventResponse, status_code=status.HTTP_201_CREATED)
def create_agenda_event(
    data: AgendaEventCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_case(db, data.case_id, user.cabinet_id)
    meet = (data.meet_url or "").strip() or None
    event = AgendaEvent(
        cabinet_id=user.cabinet_id,
        user_id=user.id,
        case_id=data.case_id,
        title=data.title.strip(),
        description=data.description,
        event_type=data.event_type,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        meet_url=meet,
        city=(data.city or "").strip() or None,
        location=(data.location or "").strip() or None,
    )
    db.add(event)
    log_audit(db, "agenda.create", user=user, request=request, details=event.title)
    db.commit()
    db.refresh(event)
    return _event_resp(db, event)


@router.patch("/agenda/{event_id}", response_model=AgendaEventResponse)
def update_agenda_event(
    event_id: str,
    data: AgendaEventUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = (
        db.query(AgendaEvent)
        .filter(AgendaEvent.id == event_id, AgendaEvent.cabinet_id == user.cabinet_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    if data.case_id is not None:
        _ensure_case(db, data.case_id or None, user.cabinet_id)
        event.case_id = data.case_id or None
    if data.title is not None:
        event.title = data.title.strip()
    if data.description is not None:
        event.description = data.description
    if data.event_type is not None:
        event.event_type = data.event_type
    if data.starts_at is not None:
        event.starts_at = data.starts_at
    if data.ends_at is not None:
        event.ends_at = data.ends_at
    if data.meet_url is not None:
        event.meet_url = data.meet_url.strip() or None
    db.commit()
    db.refresh(event)
    return _event_resp(db, event)



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
        desc = (ev.description or "").replace("\n", " ").replace(",", "\\,")
        loc_parts = [p for p in [getattr(ev, "location", None), getattr(ev, "city", None)] if p]
        loc = " — ".join(loc_parts).replace(",", "\\,")
        title = (ev.title or "Événement").replace(",", "\\,")
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


@router.delete("/agenda/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agenda_event(
    event_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = (
        db.query(AgendaEvent)
        .filter(AgendaEvent.id == event_id, AgendaEvent.cabinet_id == user.cabinet_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Événement introuvable")
    db.delete(event)
    db.commit()


_ACTION_LABELS_FR = {
    "plaidoirie.validate": "a validé une plaidoirie",
    "plaidoirie.unvalidate": "a repassé une plaidoirie en brouillon",
    "plaidoirie.draft_save": "a enregistré une plaidoirie",
    "plaidoirie.assign": "a assigné une plaidoirie",
    "plaidoirie.export_docx": "a exporté une plaidoirie (Word)",
    "plaidoirie.export_pdf": "a exporté une plaidoirie (PDF)",
    "document.upload": "a déposé un document",
    "case.create": "a créé un dossier",
    "case.update": "a modifié un dossier",
    "case.delete": "a supprimé un dossier",
    "auth.login_success": "s’est connecté(e)",
    "team.invite_email": "a envoyé une invitation d’équipe",
    "team.invite_accept": "a accepté une invitation d’équipe",
    "team.member_remove": "a retiré un membre",
    "team.role_change": "a changé un rôle",
    "agenda.create": "a créé un événement agenda",
    "billing.select_plan": "a changé de plan",
    "billing.cancel": "a demandé une résiliation",
    "payment_failed": "paiement en échec",
}


@router.get("/search", response_model=list[WorkspaceSearchHit])
def global_search(
    q: str = "",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    term = (q or "").strip()
    if len(term) < 2:
        return []
    like = f"%{term}%"
    hits: list[WorkspaceSearchHit] = []

    cases = (
        db.query(Case)
        .filter(Case.cabinet_id == user.cabinet_id)
        .filter((Case.reference.ilike(like)) | (Case.client_name.ilike(like)))
        .order_by(Case.updated_at.desc())
        .limit(8)
        .all()
    )
    for c in cases:
        hits.append(
            WorkspaceSearchHit(
                kind="case",
                id=c.id,
                title=c.reference,
                subtitle=c.client_name,
                href=f"/cases/{c.id}",
            )
        )

    docs = (
        db.query(Document)
        .filter(Document.cabinet_id == user.cabinet_id)
        .filter(Document.original_name.ilike(like))
        .order_by(Document.created_at.desc())
        .limit(8)
        .all()
    )
    for d in docs:
        hits.append(
            WorkspaceSearchHit(
                kind="document",
                id=d.id,
                title=d.original_name,
                subtitle=None,
                href=f"/documents/{d.id}",
            )
        )

    pq = db.query(PlaidoirieDraft).filter(PlaidoirieDraft.cabinet_id == user.cabinet_id)
    if user.role.value == "assistant_juridique":
        pq = pq.filter(PlaidoirieDraft.status.in_(("validated", "finalized")))
    pleas = (
        pq.filter(PlaidoirieDraft.title.ilike(like))
        .order_by(PlaidoirieDraft.updated_at.desc())
        .limit(8)
        .all()
    )
    for p in pleas:
        hits.append(
            WorkspaceSearchHit(
                kind="plaidoirie",
                id=p.id,
                title=p.title,
                subtitle=p.status,
                href="/redaction",
            )
        )
    return hits[:20]


@router.get("/activity", response_model=list[WorkspaceActivityItem])
def cabinet_activity(
    limit: int = 40,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Rétention 90 j : archive Excel auto si logs anciens (tout le cabinet voit le fil)
    try:
        from app.services.activity_archive import maybe_archive_old_activity

        maybe_archive_old_activity(db, cabinet_id=user.cabinet_id, user_id=user.id, force=False)
    except Exception:
        pass

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.cabinet_id == user.cabinet_id)
        .order_by(AuditLog.created_at.desc())
        .limit(min(limit, 80))
        .all()
    )
    user_ids = {l.user_id for l in logs if l.user_id}
    names: dict[str, str] = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            names[u.id] = u.full_name
    out: list[WorkspaceActivityItem] = []
    for log in logs:
        label = _ACTION_LABELS_FR.get(log.action, log.action.replace(".", " "))
        href = None
        if log.action.startswith("plaidoirie"):
            href = "/redaction"
        elif log.action.startswith("case"):
            href = "/cases"
        elif log.action.startswith("document"):
            href = "/documents"
        out.append(
            WorkspaceActivityItem(
                id=log.id,
                action=log.action,
                label=label,
                details=log.details,
                actor_name=names.get(log.user_id) if log.user_id else None,
                created_at=log.created_at,
                href=href,
            )
        )
    return out


@router.get("/activity/archives", response_model=list[ActivityArchiveItem])
def list_activity_archives(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ActivityArchive)
        .filter(ActivityArchive.cabinet_id == user.cabinet_id)
        .order_by(ActivityArchive.created_at.desc())
        .limit(50)
        .all()
    )
    return rows


@router.get("/activity/archives/{archive_id}/download")
def download_activity_archive(
    archive_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response

    from app.services.activity_archive import archive_bytes

    row = (
        db.query(ActivityArchive)
        .filter(
            ActivityArchive.id == archive_id,
            ActivityArchive.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Archive introuvable")
    data = archive_bytes(row)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{row.filename}"'},
    )
