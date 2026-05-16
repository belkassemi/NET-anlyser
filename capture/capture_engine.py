"""Packet capture engine using Scapy. Requires root/admin privileges."""
import logging
import queue
import threading
import time
from datetime import datetime

from scapy.all import ARP, ICMP, IP, IPv6, TCP, UDP, Ether, sniff

from classifier import classify
from geoip import lookup_country

log = logging.getLogger(__name__)

_pkt_queue: queue.Queue = queue.Queue(maxsize=10_000)
_stop_event = threading.Event()
_start_lock  = threading.Lock()
_sniff_thread: threading.Thread | None = None


# ── Packet parsing ─────────────────────────────────────────────────────────────

def _parse_packet(pkt) -> dict | None:
    """
    Extract a normalised flow record from a raw Scapy packet.
    Returns None for packets we don't care about or can't parse.
    Wrapped in a broad try/except so a single malformed frame never
    crashes the capture thread.
    """
    try:
        src_ip = dst_ip = src_port = dst_port = None
        protocol = "Other"
        pkt_bytes = len(pkt)

        if ARP in pkt:
            # Bug 10 (partial): ARP has no IP-layer ports — handled correctly
            src_ip   = pkt[ARP].psrc
            dst_ip   = pkt[ARP].pdst
            protocol = "ARP"

        elif IP in pkt:
            src_ip = pkt[IP].src
            dst_ip = pkt[IP].dst

            if TCP in pkt:
                src_port = pkt[TCP].sport
                dst_port = pkt[TCP].dport
                # Bug 9 fix: check BOTH src and dst port for HTTP detection
                if 443 in (dst_port, src_port):
                    protocol = "HTTPS"
                elif dst_port in (80, 8080) or src_port in (80, 8080):
                    protocol = "HTTP"
                else:
                    protocol = "TCP"

            elif UDP in pkt:
                src_port = pkt[UDP].sport
                dst_port = pkt[UDP].dport
                if 53 in (dst_port, src_port):
                    protocol = "DNS"
                elif dst_port in (67, 68):
                    protocol = "DHCP"
                else:
                    protocol = "UDP"

            elif ICMP in pkt:
                protocol = "ICMP"

        elif IPv6 in pkt:
            # Bug 10 fix: extract TCP/UDP ports from inside IPv6 frames
            src_ip = pkt[IPv6].src
            dst_ip = pkt[IPv6].dst

            if TCP in pkt:
                src_port = pkt[TCP].sport
                dst_port = pkt[TCP].dport
                protocol = "HTTPS" if 443 in (dst_port, src_port) else "TCP"
            elif UDP in pkt:
                src_port = pkt[UDP].sport
                dst_port = pkt[UDP].dport
                protocol = "DNS" if 53 in (dst_port, src_port) else "UDP"
            else:
                protocol = "IPv6"

        else:
            return None

        if not src_ip or not dst_ip:
            return None

        layer7  = classify(src_port, dst_port, protocol)
        country = lookup_country(dst_ip)

        return {
            "src_ip":          src_ip,
            "dst_ip":          dst_ip,
            "src_port":        src_port,
            "dst_port":        dst_port,
            "protocol":        protocol,
            "bytes":           pkt_bytes,
            "timestamp":       datetime.utcnow().isoformat(),
            "country":         country,
            "layer7_category": layer7,
        }

    except Exception:
        # Bug 5 fix: catch any malformed-packet exception so the sniff thread
        # never dies because of a single bad frame
        log.debug("Failed to parse packet", exc_info=True)
        return None


def _packet_handler(pkt) -> None:
    """Scapy callback — parse and enqueue; never raises."""
    try:
        parsed = _parse_packet(pkt)
        if parsed is None:
            return
        try:
            _pkt_queue.put_nowait(parsed)
        except queue.Full:
            # Bug fix: Drop the oldest packet to make room for real-time traffic
            try:
                _pkt_queue.get_nowait()
                _pkt_queue.put_nowait(parsed)
            except queue.Empty:
                pass
            log.debug("Packet queue full — dropped old frame")
    except Exception:
        log.debug("Unexpected error in packet handler", exc_info=True)


# ── Sniffer thread ─────────────────────────────────────────────────────────────

def _sniff_loop(iface: str | None) -> None:
    """
    Bug 6 fix: run sniff inside a restart loop.
    If Scapy crashes (interface goes down, transient OS error) the loop
    restarts after a short delay instead of silently stopping capture.
    PermissionError is fatal — no point retrying.
    """
    log.info("Sniffer starting on iface=%s", iface or "all")
    while not _stop_event.is_set():
        try:
            sniff(
                iface=iface,
                prn=_packet_handler,
                store=False,
                # Re-check the stop flag every second so shutdown is responsive
                # even when traffic is low.
                timeout=1.0,
                stop_filter=lambda _p: _stop_event.is_set(),
            )
        except PermissionError:
            log.error(
                "Permission denied — capture requires root or CAP_NET_RAW. "
                "Stopping sniffer."
            )
            _stop_event.set()
            break
        except OSError as exc:
            if _stop_event.is_set():
                break
            log.warning("Sniffer OS error (%s) — restarting in 5s", exc)
            time.sleep(5)
        except Exception as exc:
            if _stop_event.is_set():
                break
            log.warning("Sniffer crashed (%s) — restarting in 5s", exc)
            time.sleep(5)

    log.info("Sniffer thread exited")


# ── Public API ─────────────────────────────────────────────────────────────────

def start_capture(iface: str | None = None) -> threading.Thread:
    """
    Launch the sniffer in a daemon thread.
    Bug 7 fix: guarded by a lock — safe to call multiple times; only one
    thread is ever started.
    """
    global _sniff_thread
    with _start_lock:
        if _sniff_thread and _sniff_thread.is_alive():
            log.warning("Capture already running — ignoring duplicate start()")
            return _sniff_thread

        _stop_event.clear()
        _sniff_thread = threading.Thread(
            target=_sniff_loop,
            args=(iface,),
            daemon=True,
            name="scapy-sniffer",
        )
        _sniff_thread.start()
        return _sniff_thread


def stop_capture() -> None:
    """Signal the sniffer loop to exit cleanly."""
    _stop_event.set()
    if _sniff_thread:
        _sniff_thread.join(timeout=5)


def get_batch(max_size: int = 100, timeout: float = 1.0) -> list[dict]:
    """
    Drain up to *max_size* packets from the queue within *timeout* seconds.
    Bug 8 fix: changed `break` → `continue` on queue.Empty so the function
    actually waits the full timeout window before returning.  Previously, a
    100 ms gap in packet arrivals would cut the batch short even if more
    packets arrived in the remaining window.
    """
    batch: list[dict] = []
    deadline = time.monotonic() + timeout

    while len(batch) < max_size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            pkt = _pkt_queue.get(timeout=min(remaining, 0.1))
            batch.append(pkt)
        except queue.Empty:
            continue   # keep waiting until the deadline

    return batch
