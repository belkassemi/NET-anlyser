from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.traffic_log import TrafficLog
from app.schemas.traffic import TrafficLogResponse

router = APIRouter()


@router.get("/history", response_model=list[TrafficLogResponse])
async def get_history(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    protocol: Optional[str] = None,
    src_ip: Optional[str] = None,
    dst_ip: Optional[str] = None,
    since: Optional[datetime] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(TrafficLog)
    if protocol:
        q = q.filter(TrafficLog.protocol == protocol)
    if src_ip:
        q = q.filter(TrafficLog.src_ip == src_ip)
    if dst_ip:
        q = q.filter(TrafficLog.dst_ip == dst_ip)
    if since:
        q = q.filter(TrafficLog.timestamp >= since)
    return q.order_by(desc(TrafficLog.timestamp)).offset(offset).limit(limit).all()


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    now = datetime.utcnow()
    one_min_ago = now - timedelta(minutes=1)
    one_hour_ago = now - timedelta(hours=1)

    recent = db.query(TrafficLog).filter(TrafficLog.timestamp >= one_min_ago).all()
    packets_per_sec = len(recent) / 60.0
    bytes_per_sec = sum(r.bytes for r in recent) / 60.0

    protocol_counts = (
        db.query(TrafficLog.protocol, func.count(TrafficLog.id).label("count"))
        .filter(TrafficLog.timestamp >= one_hour_ago)
        .group_by(TrafficLog.protocol)
        .order_by(desc("count"))
        .all()
    )

    top_src = (
        db.query(TrafficLog.src_ip, func.sum(TrafficLog.bytes).label("total_bytes"))
        .filter(TrafficLog.timestamp >= one_hour_ago)
        .group_by(TrafficLog.src_ip)
        .order_by(desc("total_bytes"))
        .limit(10)
        .all()
    )

    top_dst = (
        db.query(TrafficLog.dst_ip, func.sum(TrafficLog.bytes).label("total_bytes"))
        .filter(TrafficLog.timestamp >= one_hour_ago)
        .group_by(TrafficLog.dst_ip)
        .order_by(desc("total_bytes"))
        .limit(10)
        .all()
    )

    return {
        "packets_per_sec": round(packets_per_sec, 2),
        "bytes_per_sec": round(bytes_per_sec, 2),
        "top_protocols": [{"protocol": p, "count": c} for p, c in protocol_counts],
        "top_talkers_src": [{"ip": ip, "bytes": b} for ip, b in top_src],
        "top_talkers_dst": [{"ip": ip, "bytes": b} for ip, b in top_dst],
        "timestamp": now.isoformat(),
    }
