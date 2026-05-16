"""
Standalone session aggregator and anomaly detector.
Runs every INTERVAL seconds in a daemon thread — no Celery or Redis required.
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.database import SessionLocal
from app.models.traffic_log import TrafficLog
from app.models.session import NetworkSession
from app.models.alert import Alert

log = logging.getLogger(__name__)

INTERVAL = 30                          # seconds — matches the task requirement
BANDWIDTH_THRESHOLD = 5 * 1024 * 1024 # 5 MB per window → high alert
PORT_SCAN_THRESHOLD = 15               # unique dst ports → scanning alert
DNS_FLOOD_THRESHOLD = 100              # DNS packets per window → medium alert
MAX_BATCH = 10_000                     # max logs per run (keeps SQLite happy)
_CHUNK = 500                           # max IDs per IN clause (SQLite param limit)


class TrafficAggregator:
    def __init__(self, interval: float = INTERVAL):
        self.interval = interval
        self._stop_event = threading.Event()   # Bug 5 fix: interruptible sleep
        self._thread: threading.Thread | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="aggregator")
        self._thread.start()
        log.info("[Aggregator] Started (interval=%ss)", self.interval)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=15)
        log.info("[Aggregator] Stopped")

    def _run(self):
        # Run once immediately so data appears without waiting a full interval
        self._safe_process()
        while not self._stop_event.wait(self.interval):  # Bug 5 fix: Event.wait is interruptible
            self._safe_process()

    def _safe_process(self):
        try:
            self.process_batch()
        except Exception:
            log.exception("[Aggregator] Unhandled error in process_batch")  # Bug 6 fix: full traceback

    # ── Core aggregation ───────────────────────────────────────────────────────

    def process_batch(self):
        db = SessionLocal()
        try:
            logs = (
                db.query(TrafficLog)
                .filter(TrafficLog.processed == False)   # noqa: E712
                .order_by(TrafficLog.timestamp)
                .limit(MAX_BATCH)
                .all()
            )
            if not logs:
                return

            log.info("[Aggregator] Processing %d unprocessed logs", len(logs))

            # ── 1. Group into flows ────────────────────────────────────────────
            flows: dict[tuple, dict] = defaultdict(lambda: {
                "bytes": 0, "packets": 0,
                "start": None, "end": None,
                "layer7": None,            # Bug 3 fix: track per flow
            })
            src_stats: dict[str, dict] = defaultdict(lambda: {
                "bytes": 0, "ports": set(), "dns_count": 0,
            })

            for row in logs:             # Bug 7 fix: renamed l → row (l looks like 1)
                key = (row.src_ip, row.dst_ip, row.src_port, row.dst_port, row.protocol)
                f = flows[key]
                f["bytes"]   += row.bytes
                f["packets"] += 1
                if row.timestamp:
                    if f["start"] is None or row.timestamp < f["start"]:
                        f["start"] = row.timestamp
                    if f["end"] is None or row.timestamp > f["end"]:
                        f["end"] = row.timestamp
                if f["layer7"] is None and row.layer7_category:  # Bug 3 fix
                    f["layer7"] = row.layer7_category

                s = src_stats[row.src_ip]
                s["bytes"] += row.bytes
                if row.dst_port:
                    s["ports"].add(row.dst_port)
                if row.protocol == "DNS" or row.dst_port == 53:
                    s["dns_count"] += 1

            # ── 2. Upsert sessions ─────────────────────────────────────────────
            hour_ago = datetime.utcnow() - timedelta(hours=1)

            for (src_ip, dst_ip, src_port, dst_port, protocol), stats in flows.items():
                if stats["start"] is None:
                    continue

                # Bug 2 fix: filter on start_time (never NULL) instead of end_time
                # (end_time is NULL when a session has only one batch → SQL NULL
                #  comparisons always return False, which caused a new duplicate
                #  session to be inserted on every aggregator run for those flows)
                existing = (
                    db.query(NetworkSession)
                    .filter(
                        NetworkSession.src_ip   == src_ip,
                        NetworkSession.dst_ip   == dst_ip,
                        NetworkSession.src_port == src_port,
                        NetworkSession.dst_port == dst_port,
                        NetworkSession.protocol == protocol,
                        NetworkSession.start_time >= hour_ago,
                    )
                    .order_by(NetworkSession.start_time.desc())
                    .first()
                )

                if existing:
                    existing.bytes   += stats["bytes"]
                    existing.packets += stats["packets"]
                    new_end = stats["end"] or stats["start"]
                    existing.end_time = max(existing.end_time or existing.start_time, new_end)
                    existing.duration = (existing.end_time - existing.start_time).total_seconds()
                else:
                    start = stats["start"]
                    end   = stats["end"] or start
                    db.add(NetworkSession(
                        src_ip=src_ip, dst_ip=dst_ip,
                        src_port=src_port, dst_port=dst_port,
                        protocol=protocol,
                        bytes=stats["bytes"],
                        packets=stats["packets"],
                        start_time=start,
                        end_time=end,
                        duration=(end - start).total_seconds(),
                        layer7_category=stats["layer7"],   # Bug 3 fix
                    ))

            # ── 3. Anomaly detection ───────────────────────────────────────────
            for src_ip, s in src_stats.items():
                bw    = s["bytes"]
                ports = s["ports"]
                dns   = s["dns_count"]

                if bw > BANDWIDTH_THRESHOLD:
                    self._alert(db, src_ip, "bandwidth", "high",
                                f"IP {src_ip} consumed {bw / 1_048_576:.1f} MB in {INTERVAL}s")

                if len(ports) > PORT_SCAN_THRESHOLD:
                    self._alert(db, src_ip, "scanning", "high",
                                f"IP {src_ip} probed {len(ports)} unique ports in {INTERVAL}s")

                if dns > DNS_FLOOD_THRESHOLD:
                    self._alert(db, src_ip, "protocol_anomaly", "medium",
                                f"IP {src_ip} sent {dns} DNS queries in {INTERVAL}s")

            # ── 4. Mark processed (chunked to respect SQLite param limit) ──────
            ids = [row.id for row in logs]
            for i in range(0, len(ids), _CHUNK):
                db.query(TrafficLog).filter(
                    TrafficLog.id.in_(ids[i : i + _CHUNK])
                ).update({"processed": True}, synchronize_session=False)

            db.commit()
            log.info("[Aggregator] Done — %d logs marked processed", len(ids))

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ── Alert helpers ──────────────────────────────────────────────────────────

    def _alert(self, db, src_ip: str, alert_type: str, severity: str, message: str):
        # Bug 4 fix: deduplicate on unresolved=False instead of a 1-minute window.
        # The old logic (created_at >= minute_ago) allowed the same alert to fire
        # once per minute for persistent conditions.  Checking unresolved=False means
        # a new alert is only created after the operator resolves the previous one.
        dup = (
            db.query(Alert)
            .filter(
                Alert.src_ip  == src_ip,
                Alert.type    == alert_type,
                Alert.resolved == False,     # noqa: E712
            )
            .first()
        )
        if not dup:
            db.add(Alert(
                src_ip=src_ip,
                type=alert_type,
                severity=severity,
                message=message,
            ))


# ── Module-level singleton ──────────────────────────────────────────────────────

_instance = TrafficAggregator()


def start(interval: float = INTERVAL) -> None:
    _instance.interval = interval
    _instance.start()


def stop() -> None:
    _instance.stop()


def process_batch() -> None:
    """Exposed for manual / test invocation."""
    _instance.process_batch()
