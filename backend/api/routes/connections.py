"""Live network connections API — real-data mode only."""

import os
from collections import defaultdict

from fastapi import APIRouter

from agent.geo_lookup import get_cached as get_geo
from agent.threat_intel import THREAT_INTEL
from agent.real_monitor import get_live_connections

SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() == "true"

router = APIRouter(prefix="/connections", tags=["connections"])


def _enrich(conn: dict) -> dict:
    """Add geo and threat-intel data to a raw connection dict."""
    rip = conn.get("remote_ip", "")

    geo = get_geo(rip) or {
        "country": "",
        "country_name": "Unknown",
        "city": "",
        "isp": "",
        "flag": "🌐",
        "is_high_risk_country": False,
        "is_suspicious_isp": False,
        "risk_geo": False,
    }

    # Quick threat intel check against static lists
    malicious = rip in THREAT_INTEL.get("malicious_ips", {})

    return {
        **conn,
        "country":              geo.get("country", ""),
        "country_name":         geo.get("country_name", ""),
        "city":                 geo.get("city", ""),
        "isp":                  geo.get("isp", ""),
        "flag":                 geo.get("flag", "🌐"),
        "is_high_risk_country": geo.get("is_high_risk_country", False),
        "is_suspicious_isp":    geo.get("is_suspicious_isp", False),
        "is_malicious_ip":      malicious,
        "is_suspicious":        malicious or geo.get("risk_geo", False),
    }


@router.get("/")
async def get_connections():
    """
    Return the current live connection table enriched with geo-IP and
    threat-intel data.  Available in real-data mode only.
    """
    if SIMULATION_MODE:
        return {
            "connections": [],
            "stats": {},
            "message": "Live connections are only available in real-data mode.",
        }

    raw = get_live_connections()
    enriched = [_enrich(c) for c in raw]

    # Build stats
    by_process: dict[str, int] = defaultdict(int)
    by_country: dict[str, int] = defaultdict(int)
    suspicious_count = 0

    for c in enriched:
        by_process[c.get("process_name", "unknown")] += 1
        country = c.get("country") or "??"
        by_country[country] += 1
        if c.get("is_suspicious"):
            suspicious_count += 1

    # Sort by connection count descending
    top_processes = sorted(by_process.items(), key=lambda x: -x[1])[:10]
    top_countries = sorted(by_country.items(), key=lambda x: -x[1])[:15]

    external = [c for c in enriched if not c.get("is_private")]
    internal = [c for c in enriched if c.get("is_private")]

    return {
        "connections": enriched,
        "stats": {
            "total":            len(enriched),
            "external":         len(external),
            "internal":         len(internal),
            "suspicious":       suspicious_count,
            "top_processes":    [{"name": p, "count": n} for p, n in top_processes],
            "top_countries":    [{"code": c, "count": n} for c, n in top_countries],
            "unique_remote_ips": len({c["remote_ip"] for c in enriched}),
        },
    }
