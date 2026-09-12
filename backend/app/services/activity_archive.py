"""Archive l'activité cabinet (>90 j) en Excel (XLSX) puis purge les logs."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from app.models import ActivityArchive, AuditLog, User
from app.services.object_storage import read_file, save_file

RETENTION_DAYS = 90


def _sheet_xml(headers: list[str], rows: list[list[str]]) -> str:
    def cell(ref: str, value: str) -> str:
        v = escape(value or "")
        return f'<c r="{ref}" t="inlineStr"><is><t>{v}</t></is></c>'

    def col_letter(i: int) -> str:
        s = ""
        n = i
        while True:
            s = chr(65 + (n % 26)) + s
            n = n // 26 - 1
            if n < 0:
                break
        return s

    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    all_rows = [headers, *rows]
    for r_idx, row in enumerate(all_rows, start=1):
        cells = "".join(cell(f"{col_letter(c)}{r_idx}", str(val)) for c, val in enumerate(row))
        lines.append(f'<row r="{r_idx}">{cells}</row>')
    lines.append("</sheetData></worksheet>")
    return "".join(lines)


def build_xlsx_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    """XLSX minimal sans dépendance (ouvre correctement dans Excel)."""
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Activite" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    wb_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", _sheet_xml(headers, rows))
    return buf.getvalue()


def maybe_archive_old_activity(
    db: Session,
    *,
    cabinet_id: str,
    user_id: str | None = None,
    force: bool = False,
) -> ActivityArchive | None:
    """Archive les logs > 90 jours (ou tous si force=False et seuil atteint)."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=RETENTION_DAYS)
    q = (
        db.query(AuditLog)
        .filter(AuditLog.cabinet_id == cabinet_id, AuditLog.created_at < cutoff)
        .order_by(AuditLog.created_at.asc())
    )
    logs = q.all()
    if not logs:
        return None
    # Éviter micro-archives : au moins 20 lignes sauf force
    if not force and len(logs) < 20:
        return None

    user_ids = {l.user_id for l in logs if l.user_id}
    names: dict[str, str] = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            names[u.id] = u.full_name

    headers = ["Date (UTC)", "Acteur", "Action", "Détails", "IP"]
    rows = [
        [
            (l.created_at.isoformat() if l.created_at else ""),
            names.get(l.user_id, "") if l.user_id else "",
            l.action or "",
            (l.details or "")[:2000],
            l.ip_address or "",
        ]
        for l in logs
    ]
    period_start = logs[0].created_at or cutoff
    period_end = logs[-1].created_at or cutoff
    stamp = now.strftime("%Y%m%d_%H%M")
    filename = f"activite_cabinet_{stamp}.xlsx"
    payload = build_xlsx_bytes(headers, rows)
    storage_path = save_file(payload, cabinet_id, "_activity_archives", ".xlsx")

    archive = ActivityArchive(
        cabinet_id=cabinet_id,
        filename=filename,
        storage_path=storage_path,
        period_start=period_start,
        period_end=period_end,
        row_count=len(logs),
        created_by=user_id,
        created_at=now,
    )
    db.add(archive)
    for l in logs:
        db.delete(l)
    db.commit()
    db.refresh(archive)
    return archive


def archive_bytes(archive: ActivityArchive) -> bytes:
    return read_file(archive.storage_path)


def also_csv_preview(headers: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerows(rows)
    return ("\ufeff" + buf.getvalue()).encode("utf-8")
