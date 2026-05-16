from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertUpdate

router = APIRouter()


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    limit: int = Query(100, le=500),
    offset: int = 0,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Alert)
    if severity:
        q = q.filter(Alert.severity == severity)
    if resolved is not None:
        q = q.filter(Alert.resolved == resolved)
    return q.order_by(desc(Alert.created_at)).offset(offset).limit(limit).all()


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    data: AlertUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = data.resolved
    if data.resolved and not alert.resolved_at:
        alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
