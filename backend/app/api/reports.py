import csv
import io
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.alert import Alert
from app.models.session import NetworkSession
from app.models.traffic_log import TrafficLog

router = APIRouter()


def _since(hours: int) -> datetime:
    return datetime.utcnow() - timedelta(hours=hours)


# ── Summary (preview before download) ─────────────────────────────────────────

@router.get("/summary")
async def summary(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Quick stats for the selected time window — powers the Reports preview panel."""
    since = _since(hours)

    total_packets = db.query(func.count(TrafficLog.id)) \
        .filter(TrafficLog.timestamp >= since).scalar() or 0

    total_bytes = db.query(func.sum(TrafficLog.bytes)) \
        .filter(TrafficLog.timestamp >= since).scalar() or 0

    total_sessions = db.query(func.count(NetworkSession.id)) \
        .filter(NetworkSession.start_time >= since).scalar() or 0

    total_alerts = db.query(func.count(Alert.id)) \
        .filter(Alert.created_at >= since).scalar() or 0

    unresolved = db.query(func.count(Alert.id)) \
        .filter(Alert.created_at >= since, Alert.resolved == False).scalar() or 0  # noqa: E712

    top_proto_row = (
        db.query(TrafficLog.protocol, func.count(TrafficLog.id).label("c"))
        .filter(TrafficLog.timestamp >= since)
        .group_by(TrafficLog.protocol)
        .order_by(desc("c"))
        .first()
    )

    return {
        "hours":            hours,
        "total_packets":    total_packets,
        "total_bytes":      total_bytes,
        "total_sessions":   total_sessions,
        "total_alerts":     total_alerts,
        "unresolved_alerts": unresolved,
        "top_protocol":     top_proto_row[0] if top_proto_row else None,
    }


# ── Export ─────────────────────────────────────────────────────────────────────

@router.get("/export")
async def export(
    format: str      = Query("csv",     regex="^(csv|json)$"),
    report_type: str = Query("traffic", regex="^(traffic|alerts|protocols|sessions)$"),
    hours: int       = Query(24, ge=1, le=168),
    db: Session      = Depends(get_db),
    _=Depends(get_current_user),
):
    since = _since(hours)

    if report_type == "traffic":
        rows = db.query(TrafficLog).filter(TrafficLog.timestamp >= since) \
            .order_by(desc(TrafficLog.timestamp)).all()
        data = [
            {
                "id": r.id, "src_ip": r.src_ip, "dst_ip": r.dst_ip,
                "src_port": r.src_port, "dst_port": r.dst_port,
                "protocol": r.protocol, "bytes": r.bytes,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "country": r.country, "layer7_category": r.layer7_category,
            }
            for r in rows
        ]

    elif report_type == "alerts":
        rows = db.query(Alert).filter(Alert.created_at >= since) \
            .order_by(desc(Alert.created_at)).all()
        data = [
            {
                "id": r.id, "type": r.type, "severity": r.severity,
                "message": r.message, "src_ip": r.src_ip,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "resolved": r.resolved,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ]

    elif report_type == "sessions":
        rows = db.query(NetworkSession).filter(NetworkSession.start_time >= since) \
            .order_by(desc(NetworkSession.start_time)).all()
        data = [
            {
                "id": r.id, "src_ip": r.src_ip, "dst_ip": r.dst_ip,
                "src_port": r.src_port, "dst_port": r.dst_port,
                "protocol": r.protocol, "layer7_category": r.layer7_category,
                "bytes": r.bytes, "packets": r.packets, "duration": r.duration,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time":   r.end_time.isoformat()   if r.end_time   else None,
            }
            for r in rows
        ]

    else:  # protocols
        rows = (
            db.query(
                TrafficLog.protocol,
                func.count(TrafficLog.id).label("count"),
                func.sum(TrafficLog.bytes).label("bytes"),
            )
            .filter(TrafficLog.timestamp >= since)
            .group_by(TrafficLog.protocol)
            .order_by(desc("bytes"))
            .all()
        )
        data = [{"protocol": p, "count": c, "bytes": b} for p, c, b in rows]

    filename = f"{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"},
        )

    # CSV
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    else:
        output.write("no data\n")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
    )
