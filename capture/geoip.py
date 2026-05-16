"""Minimal GeoIP lookup using free ip-api.com (no local DB required)."""
import logging
import ipaddress

import httpx

log = logging.getLogger(__name__)

_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

# Bug 11 fix: bound the cache so it doesn't grow forever during long captures.
# Oldest entries are evicted once the limit is reached.
_CACHE_MAXSIZE = 2048
_cache: dict[str, str | None] = {}


def _is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in _PRIVATE_RANGES)
    except ValueError:
        # Unparseable string — treat as private so we don't look it up
        return True


def _evict_oldest() -> None:
    """Remove the first (oldest) entry when the cache is full."""
    try:
        oldest = next(iter(_cache))
        del _cache[oldest]
    except StopIteration:
        pass


def lookup_country(ip: str) -> str | None:
    """
    Return the ISO country code for *ip*, or None for private/unknown addresses.
    Results are cached up to _CACHE_MAXSIZE entries.  Failed lookups are NOT
    cached so a transient network error doesn't permanently mark an IP as unknown.
    """
    if not ip:
        return None

    if _is_private(ip):
        return None

    if ip in _cache:
        return _cache[ip]

    try:
        resp = httpx.get(
            f"http://ip-api.com/json/{ip}?fields=countryCode",
            timeout=2.0,
        )
        resp.raise_for_status()
        country = resp.json().get("countryCode") or None

        # Evict oldest entry if we're at capacity before inserting
        if len(_cache) >= _CACHE_MAXSIZE:
            _evict_oldest()
        _cache[ip] = country
        return country

    except httpx.HTTPStatusError as exc:
        log.debug("GeoIP HTTP error for %s: %s", ip, exc)
        return None
    except httpx.TimeoutException:
        log.debug("GeoIP lookup timed out for %s", ip)
        return None
    except Exception as exc:
        log.debug("GeoIP lookup failed for %s: %s", ip, exc)
        return None
