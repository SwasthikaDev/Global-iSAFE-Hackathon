"""
Threat Intelligence Module
Maintains a live feed of known malicious IPs, botnet C2 servers,
and IoT-specific CVEs.  When ABUSE_IPDB_API_KEY is set, individual IPs
are checked in real-time against the AbuseIPDB v2 API.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Curated static IOC lists ──────────────────────────────────────────────────
KNOWN_MALICIOUS_IPS = {
    "185.220.101.45":  {"threat": "Mirai C2 server",              "confidence": 0.98, "category": "botnet"},
    "91.92.109.51":    {"threat": "Mozi botnet node",              "confidence": 0.95, "category": "botnet"},
    "45.142.212.100":  {"threat": "BotenaGo scanner",              "confidence": 0.92, "category": "scanner"},
    "194.165.16.11":   {"threat": "IoT credential brute-force",    "confidence": 0.97, "category": "brute_force"},
    "212.102.35.7":    {"threat": "Emotet dropper server",         "confidence": 0.91, "category": "malware"},
    "176.119.0.0":     {"threat": "Known spam/C2 netblock",        "confidence": 0.85, "category": "c2"},
    "62.204.41.252":   {"threat": "Mirai variant scanner",         "confidence": 0.96, "category": "scanner"},
    "89.248.165.0":    {"threat": "Mass IoT scanner",              "confidence": 0.88, "category": "scanner"},
    "195.54.160.149":  {"threat": "DDoS C2 infrastructure",        "confidence": 0.93, "category": "ddos"},
    "5.188.86.172":    {"threat": "Gafgyt botnet C2",              "confidence": 0.94, "category": "botnet"},
    # Simulation-only demo entries (never appear in real traffic)
    "10.0.0.99":  {"threat": "Simulated C2 server (demo)",         "confidence": 1.0, "category": "botnet_sim"},
    "10.0.0.100": {"threat": "Simulated exfil endpoint (demo)",    "confidence": 1.0, "category": "exfil_sim"},
}

KNOWN_MALICIOUS_DOMAINS = {
    "malicious-iot-c2.ru": "Mirai C2 domain",
    "botnet-update.cn":    "Botnet update server",
    "exfil-data.xyz":      "Data exfiltration endpoint",
    "iot-scanner.io":      "Autonomous IoT scanner",
    "darknet-relay.onion.to": "Tor relay / anonymisation",
}

IOT_VULNERABILITIES = [
    {
        "cve": "CVE-2023-1389",
        "device": "TP-Link Archer",
        "description": "Command injection via web management interface",
        "severity": "critical",
        "affected_ports": [80, 443, 8080],
    },
    {
        "cve": "CVE-2024-3080",
        "device": "ASUS Router",
        "description": "Authentication bypass in firmware",
        "severity": "critical",
        "affected_ports": [80, 443],
    },
    {
        "cve": "CVE-2023-48795",
        "device": "Multiple SSH implementations",
        "description": "Terrapin SSH prefix truncation attack",
        "severity": "high",
        "affected_ports": [22],
    },
    {
        "cve": "CVE-2024-21762",
        "device": "Fortinet FortiOS",
        "description": "Out-of-bounds write vulnerability",
        "severity": "critical",
        "affected_ports": [443, 8443],
    },
    {
        "cve": "CVE-2024-6387",
        "device": "OpenSSH",
        "description": "regreSSHion — unauthenticated remote code execution",
        "severity": "critical",
        "affected_ports": [22],
    },
]

# ── AbuseIPDB per-IP cache ────────────────────────────────────────────────────
# ip → (result_dict, timestamp)
_abuseipdb_cache: dict[str, tuple[dict, float]] = {}
_ABUSEIPDB_TTL = 3600.0  # 1 hour

# Global threat intel cache
_cache: dict = {}
_cache_expiry: Optional[datetime] = None
CACHE_TTL_MINUTES = 30

# Expose static data directly for the connections route
THREAT_INTEL = {
    "malicious_ips": KNOWN_MALICIOUS_IPS,
    "malicious_domains": KNOWN_MALICIOUS_DOMAINS,
}


async def get_threat_intel() -> dict:
    """Return current threat intelligence data, refreshing cache periodically."""
    global _cache, _cache_expiry

    if _cache and _cache_expiry and datetime.now() < _cache_expiry:
        return _cache

    intel = {
        "malicious_ips":     KNOWN_MALICIOUS_IPS.copy(),
        "malicious_domains": KNOWN_MALICIOUS_DOMAINS.copy(),
        "vulnerabilities":   IOT_VULNERABILITIES.copy(),
        "last_updated":      datetime.now().isoformat(),
        "feed_sources":      ["Built-in IOC list", "AbuseIPDB (live)", "CVE database"],
    }

    _cache = intel
    _cache_expiry = datetime.now() + timedelta(minutes=CACHE_TTL_MINUTES)
    return intel


async def check_ip(ip: str) -> dict:
    """
    Check a single IP against:
      1. Static IOC list (instant, no API call)
      2. AbuseIPDB real-time lookup (if ABUSE_IPDB_API_KEY is configured)
    Returns a dict with is_malicious, confidence, and source fields.
    """
    intel = await get_threat_intel()
    malicious_ips = intel["malicious_ips"]

    # --- Static list check ---
    if ip in malicious_ips:
        return {
            "is_malicious": True,
            "ip":           ip,
            "details":      malicious_ips[ip],
            "source":       "static_ioc",
        }

    # Netblock check
    parts = ip.split(".")
    if len(parts) == 4:
        netblock = f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        if netblock in malicious_ips:
            return {
                "is_malicious": True,
                "ip":           ip,
                "details":      malicious_ips[netblock],
                "source":       "static_ioc_netblock",
            }

    # --- AbuseIPDB live check ---
    abuse_result = await _abuseipdb_check(ip)
    if abuse_result:
        return abuse_result

    return {"is_malicious": False, "ip": ip, "details": None, "source": "clean"}


async def _abuseipdb_check(ip: str) -> Optional[dict]:
    """
    Check one IP against AbuseIPDB v2 Check endpoint.
    Returns None if no key is configured or lookup fails.
    Caches results for 1 hour to stay within the 1 000/day free limit.
    """
    api_key = os.getenv("ABUSE_IPDB_API_KEY", "")
    if not api_key or len(api_key) < 8:
        return None

    # Return cached result
    cached = _abuseipdb_cache.get(ip)
    if cached and time.monotonic() - cached[1] < _ABUSEIPDB_TTL:
        return cached[0]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={"Key": api_key, "Accept": "application/json"},
                params={"ipAddress": ip, "maxAgeInDays": "90", "verbose": ""},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                score = data.get("abuseConfidenceScore", 0)
                is_malicious = score >= 25  # flag if ≥25 % abuse confidence
                result = {
                    "is_malicious":     is_malicious,
                    "ip":               ip,
                    "source":           "abuseipdb",
                    "details": {
                        "threat":       "AbuseIPDB reported abuse" if is_malicious else "clean",
                        "confidence":   round(score / 100, 2),
                        "category":     "reported_abuse",
                        "country_code": data.get("countryCode", ""),
                        "isp":          data.get("isp", ""),
                        "domain":       data.get("domain", ""),
                        "total_reports": data.get("totalReports", 0),
                        "last_reported": data.get("lastReportedAt", ""),
                    } if is_malicious else None,
                }
                _abuseipdb_cache[ip] = (result, time.monotonic())
                if is_malicious:
                    logger.warning(
                        f"AbuseIPDB: {ip} has {score}% abuse score "
                        f"({data.get('totalReports', 0)} reports)"
                    )
                return result
    except Exception as exc:
        logger.debug(f"AbuseIPDB check error for {ip}: {exc}")

    return None
