"""Capture service entry point. Must run as root (or with CAP_NET_RAW)."""
import logging
import os
import signal
import sys
import time

import httpx

from capture_engine import get_batch, start_capture, stop_capture

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

# ── Configuration (all overridable via environment variables) ──────────────────

# Bug 1 fix: was "8888" — backend default port is 8000
BACKEND_URL   = os.getenv("BACKEND_URL",       "http://127.0.0.1:8888")
API_KEY       = os.getenv("INTERNAL_API_KEY",  "internal-capture-service-key")
IFACE         = os.getenv("CAPTURE_IFACE",     None)   # None = all interfaces
BATCH_INTERVAL = float(os.getenv("BATCH_INTERVAL", "1.0"))
BATCH_SIZE    = int(os.getenv("BATCH_SIZE",    "500"))
MAX_RETRIES   = int(os.getenv("MAX_RETRIES",   "3"))
RETRY_BACKOFF = float(os.getenv("RETRY_BACKOFF", "2.0"))  # seconds, multiplied by attempt
BACKEND_WAIT_ATTEMPTS = int(os.getenv("BACKEND_WAIT_ATTEMPTS", "10"))
BACKEND_WAIT_DELAY    = float(os.getenv("BACKEND_WAIT_DELAY",  "3.0"))

_running = True


# ── Graceful shutdown ──────────────────────────────────────────────────────────

def _on_shutdown(signum, _frame) -> None:
    # Bug 2 fix: handle SIGINT / SIGTERM cleanly instead of crashing
    global _running
    log.info("Signal %d received — shutting down gracefully...", signum)
    _running = False
    stop_capture()


# ── Backend health check ───────────────────────────────────────────────────────

def _wait_for_backend() -> bool:
    """
    Ping /health until the backend responds or we run out of attempts.
    Prevents capture from starting before the backend is ready to accept data.
    """
    log.info("Waiting for backend at %s ...", BACKEND_URL)
    for attempt in range(1, BACKEND_WAIT_ATTEMPTS + 1):
        try:
            resp = httpx.get(f"{BACKEND_URL}/health", timeout=5.0)
            if resp.status_code == 200:
                log.info("Backend is reachable (attempt %d)", attempt)
                return True
            log.warning(
                "Backend returned HTTP %d (attempt %d/%d)",
                resp.status_code, attempt, BACKEND_WAIT_ATTEMPTS,
            )
        except httpx.ConnectError:
            log.warning(
                "Backend not reachable yet (attempt %d/%d) — retrying in %.0fs",
                attempt, BACKEND_WAIT_ATTEMPTS, BACKEND_WAIT_DELAY,
            )
        except httpx.TimeoutException:
            log.warning(
                "Health-check timed out (attempt %d/%d)", attempt, BACKEND_WAIT_ATTEMPTS
            )
        except Exception as exc:
            log.warning(
                "Health-check error: %s (attempt %d/%d)", exc, attempt, BACKEND_WAIT_ATTEMPTS
            )

        if attempt < BACKEND_WAIT_ATTEMPTS:
            time.sleep(BACKEND_WAIT_DELAY)

    log.error("Backend unreachable after %d attempts — aborting", BACKEND_WAIT_ATTEMPTS)
    return False


# ── Batch sender with retry ────────────────────────────────────────────────────

def send_batch(packets: list[dict]) -> bool:
    """
    POST a packet batch to the backend.
    Bug 4 fix: retries up to MAX_RETRIES times with linear back-off before
    dropping the batch and logging an error.  Distinguishes client errors
    (4xx) from transient errors to avoid retrying hopeless requests.
    Returns True if the batch was accepted, False otherwise.
    """
    if not packets:
        return True

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/api/internal/batch",
                json=packets,
                headers={"x-api-key": API_KEY},
                timeout=15.0,
            )
            resp.raise_for_status()
            log.info("Sent %d packets → HTTP %d", len(packets), resp.status_code)
            return True

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body   = exc.response.text[:200]
            log.warning(
                "Backend rejected batch HTTP %d: %s (attempt %d/%d)",
                status, body, attempt, MAX_RETRIES,
            )
            # Client errors (auth, bad payload) will not improve on retry
            if status in (400, 401, 403, 422):
                log.error("Non-retryable client error — dropping batch of %d packets", len(packets))
                return False

        except httpx.ConnectError:
            log.warning("Cannot reach backend (attempt %d/%d)", attempt, MAX_RETRIES)

        except httpx.TimeoutException:
            log.warning("Request timed out (attempt %d/%d)", attempt, MAX_RETRIES)

        except Exception as exc:
            log.warning(
                "Unexpected send error: %s (attempt %d/%d)", exc, attempt, MAX_RETRIES
            )

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF * attempt
            log.info("Retrying in %.1fs...", wait)
            time.sleep(wait)

    log.error(
        "Dropping batch of %d packets after %d failed attempts",
        len(packets), MAX_RETRIES,
    )
    return False


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    global _running

    # Bug 2 fix: register signal handlers for clean shutdown
    signal.signal(signal.SIGINT,  _on_shutdown)
    signal.signal(signal.SIGTERM, _on_shutdown)

    log.info(
        "NetAnalyzer capture engine | backend=%s | iface=%s | batch=%d pkts/%.1fs",
        BACKEND_URL, IFACE or "all", BATCH_SIZE, BATCH_INTERVAL,
    )

    # Don't start sniffing if the backend isn't ready
    if not _wait_for_backend():
        sys.exit(1)

    # Bug 3 fix: wrap start_capture() so permission errors are caught and
    # reported clearly instead of propagating as an unhandled exception
    try:
        start_capture(iface=IFACE)
    except PermissionError:
        log.error(
            "Permission denied — capture requires root privileges or CAP_NET_RAW.\n"
            "  Linux:   sudo python main.py\n"
            "  Docker:  privileged: true + network_mode: host"
        )
        sys.exit(1)
    except Exception:
        log.exception("Failed to start capture engine")
        sys.exit(1)

    log.info("Capture running — press Ctrl+C to stop")

    # Main drain loop
    while _running:
        try:
            batch = get_batch(max_size=BATCH_SIZE, timeout=BATCH_INTERVAL)
            if batch:
                send_batch(batch)
        except Exception:
            log.exception("Unexpected error in main loop — continuing")
            time.sleep(1.0)   # brief pause to avoid spinning on a persistent error

    log.info("Capture service stopped")


if __name__ == "__main__":
    main()
