"""
Async TCP Port Scanner for LAN Devices
Probes common IoT / router ports on each discovered device and classifies
risk by service type.  Uses asyncio so the main agent loop never blocks.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Port → (service name, risk level) ────────────────────────────────────────
PORTS: dict[int, tuple[str, str]] = {
    21:   ("FTP",          "high"),      # Unencrypted file transfer
    22:   ("SSH",          "low"),
    23:   ("Telnet",       "critical"),  # Plaintext shell — Mirai uses this
    25:   ("SMTP",         "medium"),
    53:   ("DNS",          "low"),
    80:   ("HTTP",         "low"),
    443:  ("HTTPS",        "none"),
    445:  ("SMB",          "high"),      # EternalBlue / WannaCry vector
    554:  ("RTSP",         "medium"),    # IP camera streams
    1080: ("SOCKS Proxy",  "high"),
    1883: ("MQTT",         "high"),      # Unencrypted MQTT broker
    3389: ("RDP",          "high"),      # Remote desktop — brute-forced often
    4444: ("Metasploit",   "critical"),  # Classic RAT listener port
    5000: ("UPnP / Dev",   "medium"),
    5555: ("ADB",          "critical"),  # Android Debug Bridge
    5900: ("VNC",          "high"),
    7547: ("TR-069",       "critical"),  # Router mgmt — Mirai / Masscan target
    8080: ("HTTP-Alt",     "low"),
    8443: ("HTTPS-Alt",    "low"),
    8554: ("RTSP-Alt",     "medium"),
    8888: ("HTTP-Dev",     "low"),
    9000: ("Admin Portal", "medium"),
    9001: ("Tor",          "high"),
}

RISK_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}

# Results are cached here: device_id → scan dict
_results: dict[str, dict] = {}


async def _probe(ip: str, port: int, timeout: float = 0.7) -> bool:
    """Return True if the TCP port is open (connection accepted)."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout,
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


async def scan_device(device_id: str, ip: str) -> dict:
    """
    Scan all ports in PORTS concurrently for the given IP.
    Returns and stores a scan result dict.
    """
    tasks = {port: _probe(ip, port) for port in PORTS}
    results_raw = await asyncio.gather(*tasks.values(), return_exceptions=True)

    open_ports: list[dict] = []
    for (port, (service, risk)), is_open in zip(PORTS.items(), results_raw):
        if is_open is True:
            open_ports.append({"port": port, "service": service, "risk": risk})
            logger.info(f"Port scan {ip}:{port} OPEN ({service}, {risk})")

    # Determine overall risk
    max_risk = max(
        (RISK_ORDER[p["risk"]] for p in open_ports),
        default=0,
    )
    overall = {v: k for k, v in RISK_ORDER.items()}[max_risk]

    dangerous = [p for p in open_ports if p["risk"] in ("critical", "high")]

    result = {
        "device_id":    device_id,
        "ip":           ip,
        "open_ports":   open_ports,
        "dangerous_ports": dangerous,
        "risk_level":   overall,
        "scan_time":    datetime.now().isoformat(),
        "total_open":   len(open_ports),
    }
    _results[device_id] = result
    return result


def get_scan_result(device_id: str) -> Optional[dict]:
    return _results.get(device_id)


def get_all_scan_results() -> dict[str, dict]:
    return dict(_results)


async def scan_all_devices(devices: list[dict]) -> None:
    """
    Scan all registered devices concurrently.
    Skips 'local-machine' (scanning localhost is not useful here).
    """
    targets = [d for d in devices if d.get("id") != "local-machine"]
    if not targets:
        return
    logger.info(f"Starting port scan on {len(targets)} device(s)...")
    await asyncio.gather(
        *(scan_device(d["id"], d["ip"]) for d in targets),
        return_exceptions=True,
    )
    logger.info("Port scan complete.")
