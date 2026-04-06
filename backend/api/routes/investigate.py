"""
IP Investigation Endpoint
Given any IP address (LAN or public), run a parallel set of checks:
  - Reverse DNS
  - Geolocation (public IPs)
  - Threat intelligence (static IOC + AbuseIPDB)
  - Reachability (ICMP ping)
  - Port scan (LAN IPs only, capped to 20 most common ports)
  - Active connection list (from live connection snapshot)
  - Registered device lookup
"""

import asyncio
import logging
import re
import socket
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.geo_lookup import lookup_ip
from agent.threat_intel import check_ip
from agent.real_monitor import get_live_connections
from agent.monitor import get_all_devices
from agent.port_scanner import PORTS, _probe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investigate", tags=["investigate"])

# Ports to probe for general IP investigation (faster subset)
INVESTIGATE_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 443: "HTTPS", 445: "SMB", 554: "RTSP",
    1883: "MQTT", 3389: "RDP", 5555: "ADB", 7547: "TR-069",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 8554: "RTSP-Alt",
    9001: "Tor", 5900: "VNC", 4444: "Metasploit", 1080: "SOCKS",
}

PORT_RISK = {p: r for p, (_, r) in PORTS.items()}


def _is_private(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return (
        a == 10
        or (a == 172 and 16 <= b <= 31)
        or (a == 192 and b == 168)
        or a == 127
    )


def _valid_ip(ip: str) -> bool:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, ip):
        return False
    return all(0 <= int(o) <= 255 for o in ip.split("."))


async def _reverse_dns(ip: str) -> str:
    try:
        loop = asyncio.get_event_loop()
        hostname = await loop.run_in_executor(None, lambda: socket.gethostbyaddr(ip)[0])
        return hostname
    except Exception:
        return ip


async def _ping(ip: str) -> tuple[bool, Optional[float]]:
    """Return (is_alive, latency_ms)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-n", "1", "-w", "800", ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        output = stdout.decode(errors="ignore")
        alive = proc.returncode == 0
        # Parse latency from "time=2ms"
        m = re.search(r"time[=<](\d+)ms", output)
        latency = float(m.group(1)) if m else None
        return alive, latency
    except Exception:
        return False, None


async def _scan_ports(ip: str) -> list[dict]:
    """Scan INVESTIGATE_PORTS concurrently."""
    tasks = {port: _probe(ip, port, timeout=0.6) for port in INVESTIGATE_PORTS}
    results_raw = await asyncio.gather(*tasks.values(), return_exceptions=True)
    open_ports = []
    for (port, service), is_open in zip(INVESTIGATE_PORTS.items(), results_raw):
        if is_open is True:
            risk = PORT_RISK.get(port, "low")
            open_ports.append({"port": port, "service": service, "risk": risk})
    return open_ports


def _get_connections_for_ip(ip: str) -> list[dict]:
    """Find all live connections that involve this IP."""
    conns = get_live_connections()
    matches = []
    for c in conns:
        if c.get("remote_ip") == ip or c.get("local_ip") == ip:
            matches.append({
                "local_port":   c.get("local_port"),
                "remote_ip":    c.get("remote_ip"),
                "remote_port":  c.get("remote_port"),
                "protocol":     c.get("protocol"),
                "process_name": c.get("process_name"),
                "hostname":     c.get("hostname"),
            })
    return matches


async def _empty_list() -> list:
    return []


def _get_registered_device(ip: str) -> Optional[dict]:
    """Check if this IP belongs to a registered monitored device."""
    for device in get_all_devices():
        if device.get("ip") == ip:
            return {
                "id":           device["id"],
                "name":         device["name"],
                "type":         device["type"],
                "manufacturer": device.get("manufacturer", ""),
                "mac":          device.get("mac", ""),
                "status":       device.get("status", ""),
                "threat_level": device.get("threat_level", ""),
            }
    return None


# ── Main investigation endpoint ───────────────────────────────────────────────

@router.get("/{ip}")
async def investigate(ip: str):
    """
    Run a full parallel intelligence investigation on the given IP address.
    Returns geolocation, threat intel, reachability, open ports (LAN), and
    a list of active connections from this machine to/from that IP.
    """
    ip = ip.strip()
    if not _valid_ip(ip):
        raise HTTPException(status_code=422, detail=f"Invalid IP address: {ip!r}")

    private = _is_private(ip)

    # Run all checks concurrently
    (
        hostname,
        geo,
        threat,
        ping_result,
        open_ports,
    ) = await asyncio.gather(
        _reverse_dns(ip),
        lookup_ip(ip),
        check_ip(ip),
        _ping(ip),
        _scan_ports(ip) if private else _empty_list(),
    )

    is_alive, latency_ms = ping_result

    # Active connections (synchronous, fast)
    active_conns = _get_connections_for_ip(ip)
    registered   = _get_registered_device(ip)

    # Determine overall risk
    risk = "none"
    if threat.get("is_malicious"):
        risk = "critical"
    elif geo.get("risk_geo"):
        risk = "high"
    elif any(p["risk"] in ("critical", "high") for p in open_ports):
        risk = max((p["risk"] for p in open_ports), key=lambda r: {"critical": 3, "high": 2, "medium": 1, "low": 0, "none": -1}.get(r, 0))
    elif open_ports:
        risk = "low"

    return {
        "ip":             ip,
        "hostname":       hostname,
        "is_private":     private,
        "is_alive":       is_alive,
        "latency_ms":     latency_ms,
        "scanned_at":     datetime.now().isoformat(),
        "risk_level":     risk,

        # Geolocation
        "country":        geo.get("country", ""),
        "country_name":   geo.get("country_name", ""),
        "city":           geo.get("city", ""),
        "isp":            geo.get("isp", ""),
        "org":            geo.get("org", ""),
        "flag":           geo.get("flag", "🌐"),
        "is_high_risk_country": geo.get("is_high_risk_country", False),
        "is_suspicious_isp":    geo.get("is_suspicious_isp", False),

        # Threat intel
        "is_malicious":   threat.get("is_malicious", False),
        "threat_details": threat.get("details"),
        "threat_source":  threat.get("source", "clean"),

        # Port scan (LAN only)
        "open_ports":     open_ports,
        "dangerous_ports": [p for p in open_ports if p["risk"] in ("critical", "high")],

        # Connectivity
        "active_connections": active_conns,
        "connection_count":   len(active_conns),

        # Registered device
        "registered_device": registered,
    }
