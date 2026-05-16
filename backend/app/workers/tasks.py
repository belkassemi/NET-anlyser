from datetime import datetime, timedelta
from app.workers.celery_app import celery_app

# Per-IP connection counter stored in Redis for scanning detection
_SCAN_WINDOW = 60  # seconds
_SCAN_THRESHOLD = 50  # connections per minute → scanning alert
_BANDWIDTH_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB/s


@celery_app.task
def check_anomalies(src_ip: str, dst_ip: str, pkt_bytes: int, protocol: str):
    from app.core.database import SessionLocal
    from app.models.traffic_log import TrafficLog
    from app.models.alert import Alert
    import redis
    from app.core.config import settings

    r = redis.from_url(settings.REDIS_URL)
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        one_min_ago = now - timedelta(minutes=1)

        # --- Port scanning: many unique dst_ports from same src_ip ---
        key = f"scan:{src_ip}"
        r.incr(key)
        r.expire(key, _SCAN_WINDOW)
        count = int(r.get(key) or 0)
        if count > _SCAN_THRESHOLD:
            _create_alert(db, "scanning", "high", f"Port scan detected from {src_ip}", src_ip)
            r.delete(key)

        # --- Bandwidth spike: total bytes from src in last minute ---
        bw_key = f"bw:{src_ip}"
        r.incrby(bw_key, pkt_bytes)
        r.expire(bw_key, _SCAN_WINDOW)
        total_bytes = int(r.get(bw_key) or 0)
        if total_bytes > _BANDWIDTH_THRESHOLD_BYTES:
            _create_alert(db, "bandwidth", "medium", f"High bandwidth from {src_ip}: {total_bytes // 1024} KB/min", src_ip)
            r.delete(bw_key)

        # --- Excessive DNS queries ---
        if protocol == "DNS":
            dns_key = f"dns:{src_ip}"
            r.incr(dns_key)
            r.expire(dns_key, _SCAN_WINDOW)
            dns_count = int(r.get(dns_key) or 0)
            if dns_count > 200:
                _create_alert(db, "protocol_anomaly", "medium", f"Excessive DNS queries from {src_ip}: {dns_count}/min", src_ip)
                r.delete(dns_key)

    finally:
        db.close()


def _create_alert(db, alert_type, severity, message, src_ip=None):
    from app.models.alert import Alert
    # Avoid duplicate unresolved alerts
    existing = (
        db.query(Alert)
        .filter(Alert.type == alert_type, Alert.src_ip == src_ip, Alert.resolved == False)
        .first()
    )
    if not existing:
        db.add(Alert(type=alert_type, severity=severity, message=message, src_ip=src_ip))
        db.commit()


@celery_app.task
def mark_offline_devices():
    from app.core.database import SessionLocal
    from app.models.device import Device
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() - timedelta(minutes=5)
        db.query(Device).filter(Device.last_seen < threshold, Device.status == True).update({"status": False})
        db.commit()
    finally:
        db.close()


@celery_app.task
def cleanup_old_logs():
    from app.core.database import SessionLocal
    from app.models.traffic_log import TrafficLog
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        db.query(TrafficLog).filter(TrafficLog.timestamp < cutoff).delete()
        db.commit()
    finally:
        db.close()
