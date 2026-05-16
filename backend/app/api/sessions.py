from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.session import NetworkSession
from app.schemas.session import SessionResponse

router = APIRouter()


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    limit: int = Query(100, le=500),
    offset: int = 0,
    protocol: Optional[str] = None,
    src_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(NetworkSession)
    if protocol:
        q = q.filter(NetworkSession.protocol == protocol)
    if src_ip:
        q = q.filter(NetworkSession.src_ip == src_ip)
    return q.order_by(desc(NetworkSession.start_time)).offset(offset).limit(limit).all()
