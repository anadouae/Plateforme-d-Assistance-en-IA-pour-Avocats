"""WebSocket temps réel — sync multi-navigateurs par cabinet."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import User
from app.services.realtime import subscribe_cabinet

logger = logging.getLogger(__name__)
router = APIRouter(tags=["realtime"])


def _user_from_token(token: str) -> User | None:
    """Accepte uniquement un access JWT (pas refresh) + utilisateur actif."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        uid = payload.get("sub")
        if not uid:
            return None
    except JWTError:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == uid, User.is_active.is_(True)).first()
        if not user:
            return None
        # Session optionnelle : si sid présent, vérifier qu'elle n'est pas révoquée
        sid = payload.get("sid")
        if sid:
            from app.services.auth_sessions import session_is_active

            if not session_is_active(db, sid):
                return None
        return user
    finally:
        db.close()


@router.websocket("/api/ws/cabinet")
async def cabinet_ws(websocket: WebSocket, token: str = Query("")):
    await websocket.accept()
    user = _user_from_token(token or "")
    if not user or not user.cabinet_id:
        await websocket.close(code=4401)
        return
    cabinet_id = user.cabinet_id
    try:
        await websocket.send_json({"event": "connected", "payload": {"cabinet_id": cabinet_id}})
        async for raw in subscribe_cabinet(cabinet_id):
            try:
                await websocket.send_text(raw)
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("cabinet_ws error")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
