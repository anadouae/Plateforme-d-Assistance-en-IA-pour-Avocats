"""Notes, tâches et agenda cabinet — workspace léger type ClickUp juridique."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, log_audit
from app.core.database import get_db
from app.models import AgendaEvent, Case, CaseNote, CaseTask, User
from app.schemas import (
    AgendaEventCreate,
    AgendaEventResponse,
    AgendaEventUpdate,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteUpdate,
    CaseTaskCreate,
    CaseTaskResponse,
    CaseTaskUpdate,
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


def _task_resp(db: Session, task: CaseTask) -> CaseTaskResponse:
    return CaseTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        case_id=task.case_id,
        case_reference=_case_ref(db, task.case_id, task.cabinet_id),
        status=task.status,
        due_at=task.due_at,
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
