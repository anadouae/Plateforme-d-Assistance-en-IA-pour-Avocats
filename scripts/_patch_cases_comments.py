# -*- coding: utf-8 -*-
"""Append case comments endpoints."""
from pathlib import Path

p = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\backend\app\api\cases.py")
t = p.read_text(encoding="utf-8")

if "list_case_comments" in t:
    print("already")
else:
    t = t.replace(
        "from app.models import (\n    AgendaEvent,\n    Case,\n    CaseNote,\n    CaseTask,\n    Document,\n    PlaidoirieDraft,\n    User,\n    UserRole,\n)",
        "from app.models import (\n    AgendaEvent,\n    Case,\n    CaseComment,\n    CaseNote,\n    CaseTask,\n    Document,\n    PlaidoirieDraft,\n    User,\n    UserRole,\n)",
        1,
    )
    t = t.replace(
        "from app.schemas import CaseAnalysisResponse, CaseCreate, CaseResponse, CaseUpdate",
        "from app.schemas import (\n"
        "    CaseAnalysisResponse,\n"
        "    CaseCommentCreate,\n"
        "    CaseCommentResponse,\n"
        "    CaseCreate,\n"
        "    CaseResponse,\n"
        "    CaseUpdate,\n"
        ")",
        1,
    )
    t = t.replace(
        "    db.query(PlaidoirieDraft).filter(PlaidoirieDraft.case_id == case.id).delete(\n"
        "        synchronize_session=False\n"
        "    )",
        "    db.query(PlaidoirieDraft).filter(PlaidoirieDraft.case_id == case.id).delete(\n"
        "        synchronize_session=False\n"
        "    )\n"
        "    db.query(CaseComment).filter(CaseComment.case_id == case.id).delete(\n"
        "        synchronize_session=False\n"
        "    )",
        1,
    )

    append = '''

def _get_case_or_404(db: Session, case_id: str, cabinet_id: str) -> Case:
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.cabinet_id == cabinet_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")
    return case


@router.get("/{case_id}/comments", response_model=list[CaseCommentResponse])
def list_case_comments(
    case_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_case_or_404(db, case_id, user.cabinet_id)
    rows = (
        db.query(CaseComment)
        .filter(CaseComment.case_id == case_id, CaseComment.cabinet_id == user.cabinet_id)
        .order_by(CaseComment.created_at.asc())
        .limit(200)
        .all()
    )
    out = []
    for row in rows:
        author = db.query(User).filter(User.id == row.user_id).first()
        out.append(
            CaseCommentResponse(
                id=row.id,
                case_id=row.case_id,
                body=row.body,
                author_name=author.full_name if author else "",
                created_at=row.created_at,
            )
        )
    return out


@router.post("/{case_id}/comments", response_model=CaseCommentResponse, status_code=status.HTTP_201_CREATED)
def add_case_comment(
    case_id: str,
    data: CaseCommentCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = _get_case_or_404(db, case_id, user.cabinet_id)
    row = CaseComment(
        cabinet_id=user.cabinet_id,
        case_id=case.id,
        user_id=user.id,
        body=data.body.strip(),
    )
    db.add(row)
    case.updated_at = datetime.now(timezone.utc)
    log_audit(db, "case.comment", user=user, request=request, details=case.reference)
    db.commit()
    db.refresh(row)
    return CaseCommentResponse(
        id=row.id,
        case_id=row.case_id,
        body=row.body,
        author_name=user.full_name,
        created_at=row.created_at,
    )


@router.delete("/{case_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case_comment(
    case_id: str,
    comment_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_case_or_404(db, case_id, user.cabinet_id)
    row = (
        db.query(CaseComment)
        .filter(
            CaseComment.id == comment_id,
            CaseComment.case_id == case_id,
            CaseComment.cabinet_id == user.cabinet_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Commentaire introuvable")
    if row.user_id != user.id and user.role not in (UserRole.ADMIN_CABINET, UserRole.ADMIN_WEBVOICE):
        raise HTTPException(status_code=403, detail="Non autorisé")
    log_audit(db, "case.comment_delete", user=user, request=request, details=case_id)
    db.delete(row)
    db.commit()
'''
    t = t.rstrip() + "\n" + append + "\n"
    tmp = p.with_suffix(".py.wtmp")
    tmp.write_text(t, encoding="utf-8")
    p.write_bytes(tmp.read_bytes())
    tmp.unlink(missing_ok=True)
    print("cases comments OK")
