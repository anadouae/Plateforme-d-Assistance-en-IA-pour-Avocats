
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
