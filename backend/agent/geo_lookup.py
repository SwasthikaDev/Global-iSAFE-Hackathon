"""
IP Geolocation Service
Uses the free ip-api.com batch API (45 req/min, no key required).
All results are cached for 1 hour to stay well within rate limits.
Private / LAN addresses are resolved locally without any API call.
"""

import asyncio
import logging
import time
from collections import deque
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Country flag emoji lookup ─────────────────────────────────────────────────
def _flag(code: str) -> str:
    """Convert ISO 3166-1 alpha-2 country code to emoji flag."""
    if not code or len(code) != 2:
        return "🌐"
    return chr(0x1F1E6 + ord(code[0]) - ord("A")) + chr(0x1F1E6 + ord(code[1]) - ord("A"))


# Country codes considered elevated-risk for home IoT traffic
HIGH_RISK_COUNTRIES = {"RU", "CN", "KP", "IR", "NG", "BY", "VN", "UA"}

# ISP / hosting keywords that indicate a VPS / bulletproof host
_SUSPICIOUS_ISP_KEYWORDS = {
    "choopa", "vultr", "linode", "digitalocean", "hetzner", "ovh", "m247",
    "serverius", "frantech", "buyvm", "privatelayer", "psychz",
}

# ── In-memory LRU-style cache ─────────────────────────────────────────────────
_cache: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 3600.0  # seconds

# Pending IPs waiting for the next batch flush
_pending: set[str] = set()
_flush_lock = asyncio.Lock()


def _is_private(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return True
    return a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168) or a == 127


def _lan_result() -> dict:
    return {
        "country": "LAN",
        "country_name": "Local Network",
        "city": "LAN",
        "isp": "Local Network",
        "org": "",
        "flag": "🏠",
        "is_high_risk_country": False,
        "is_suspicious_isp": False,
        "risk_geo": False,
    }


def _make_result(raw: dict) -> dict:
    code = raw.get("countryCode", "")
    isp  = raw.get("isp", "").lower()
    org  = raw.get("org", "").lower()
    suspicious_isp = any(k in isp or k in org for k in _SUSPICIOUS_ISP_KEYWORDS)
    high_risk      = code in HIGH_RISK_COUNTRIES
    return {
        "country":              code,
        "country_name":         raw.get("country", "Unknown"),
        "city":                 raw.get("city", ""),
        "isp":                  raw.get("isp", ""),
        "org":                  raw.get("org", ""),
        "flag":                 _flag(code),
        "is_high_risk_country": high_risk,
        "is_suspicious_isp":    suspicious_isp,
        "risk_geo":             high_risk or suspicious_isp,
    }


def _unknown_result() -> dict:
    return {
        "country": "??",
        "country_name": "Unknown",
        "city": "",
        "isp": "Unknown",
        "org": "",
        "flag": "🌐",
        "is_high_risk_country": False,
        "is_suspicious_isp": False,
        "risk_geo": False,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_cached(ip: str) -> Optional[dict]:
    """Return cached geo result or None."""
    entry = _cache.get(ip)
    if entry and time.monotonic() - entry[1] < _CACHE_TTL:
        return entry[0]
    return None


async def lookup_ip(ip: str) -> dict:
    """Look up a single IP (cached; no API call for private IPs)."""
    if _is_private(ip):
        return _lan_result()
    cached = get_cached(ip)
    if cached:
        return cached
    # Not cached — do a single lookup
    result = await _batch_fetch([ip])
    return result.get(ip, _unknown_result())


async def enqueue_ips(ips: list[str]) -> None:
    """Queue a set of public IPs for the next batch flush."""
    for ip in ips:
        if not _is_private(ip) and not get_cached(ip):
            _pending.add(ip)


async def flush_pending() -> None:
    """Drain the pending queue and resolve up to 100 IPs via the batch API."""
    async with _flush_lock:
        if not _pending:
            return
        batch = list(_pending)[:100]
        for ip in batch:
            _pending.discard(ip)
        results = await _batch_fetch(batch)
        for ip, result in results.items():
            _cache[ip] = (result, time.monotonic())


async def _batch_fetch(ips: list[str]) -> dict[str, dict]:
    """POST to ip-api.com/batch and return {ip: result_dict}."""
    if not ips:
        return {}
    payload = [
        {"query": ip, "fields": "status,countryCode,country,city,isp,org,query"}
        for ip in ips
    ]
    out: dict[str, dict] = {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post("http://ip-api.com/batch", json=payload)
            if r.status_code == 200:
                for item in r.json():
                    q = item.get("query", "")
                    if q and item.get("status") == "success":
                        out[q] = _make_result(item)
                    elif q:
                        out[q] = _unknown_result()
    except Exception as exc:
        logger.debug(f"ip-api.com batch error: {exc}")
    return out


# ── Background flusher ────────────────────────────────────────────────────────

async def geo_background_task() -> None:
    """Runs forever; flushes pending geo queue every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        try:
            await flush_pending()
        except Exception as exc:
            logger.debug(f"geo flush error: {exc}")
