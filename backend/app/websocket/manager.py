import asyncio
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import func, desc
from app.core.database import SessionLocal
from app.models.traffic_log import TrafficLog
from app.models.alert import Alert

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def _build_metrics() -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        window = now - timedelta(minutes=5)
        one_hour_ago = now - timedelta(hours=1)

        recent = db.query(TrafficLog).filter(TrafficLog.timestamp >= window).all()

        packets_per_sec = round(len(recent) / 300.0, 2)
        bytes_per_sec   = round(sum(r.bytes for r in recent) / 300.0, 2)

        # Fast: protocol counts from already-loaded recent rows
        from collections import Counter
        proto_counts = Counter(r.protocol for r in recent)
        protocol_rows = sorted(proto_counts.items(), key=lambda x: -x[1])[:8]

        # Fast: top talkers from already-loaded recent rows (in-memory)
        from collections import defaultdict
        src_bytes: dict = defaultdict(int)
        for r in recent:
            src_bytes[r.src_ip] += r.bytes
        top_src = sorted(src_bytes.items(), key=lambda x: -x[1])[:5]

        unresolved_alerts = db.query(func.count(Alert.id)).filter(Alert.resolved == False).scalar()

        latest_row = (
            db.query(Alert)
            .filter(Alert.resolved == False)
            .order_by(desc(Alert.created_at))
            .first()
        )
        latest_alert = {
            "id":         latest_row.id,
            "type":       latest_row.type,
            "severity":   latest_row.severity,
            "message":    latest_row.message,
            "src_ip":     latest_row.src_ip,
            "created_at": latest_row.created_at.isoformat(),
        } if latest_row else None

        return {
            "packets_per_sec":    packets_per_sec,
            "bytes_per_sec":      bytes_per_sec,
            "active_connections": len(recent),
            "unresolved_alerts":  unresolved_alerts,
            "top_protocols":      [{"protocol": p, "count": c} for p, c in protocol_rows],
            "top_talkers_src":    [{"ip": ip, "bytes": int(b)} for ip, b in top_src],
            "latest_alert":       latest_alert,
            "timestamp":          now.isoformat(),
        }
    finally:
        db.close()



@router.websocket("/ws/live")
async def live_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        loop = asyncio.get_event_loop()
        while True:
            # Run the blocking DB call in a thread pool so the event loop stays free
            metrics = await loop.run_in_executor(None, _build_metrics)
            await websocket.send_json(metrics)
            await asyncio.sleep(3)  # Update every 3 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception("WebSocket error: %s", exc)
        manager.disconnect(websocket)
