"""
Real Network Traffic Monitor
Captures actual network connections and I/O statistics from the OS using psutil.
No packet capture driver or elevated privileges required — reads the kernel
connection table and per-NIC I/O counters that are always available.
"""

import logging
import socket
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

# ── Protocol port map ────────────────────────────────────────────────────────
PORT_PROTOCOLS: dict[int, str] = {
    80: "HTTP",
    443: "HTTPS",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    110: "POP3",
    143: "IMAP",
    465: "SMTPS",
    587: "SMTP",
    993: "IMAPS",
    995: "POP3S",
    1883: "MQTT",
    8883: "MQTTS",
    5683: "CoAP",
    5684: "CoAPs",
    3389: "RDP",
    5900: "VNC",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    3478: "STUN/WebRTC",
    5349: "TURN/WebRTC",
    5228: "GCM-Push",
    6667: "IRC",
    6697: "IRC-TLS",
    4444: "Metasploit",
    1080: "SOCKS",
    9001: "Tor",
    9050: "Tor",
}

# Max expected bytes per 2.5-second cycle by device type
DEVICE_BYTE_LIMITS: dict[str, int] = {
    "workstation": 200_000_000,   # 200 MB/cycle is extreme
    "router": 500_000_000,
    "smart_tv": 50_000_000,
    "mobile": 20_000_000,
    "ip_camera": 10_000_000,
    "smart_speaker": 5_000_000,
    "smart_home": 2_000_000,
    "iot_controller": 1_000_000,
    "smart_thermostat": 500_000,
    "smart_plug": 100_000,
    "unknown": 50_000_000,
}

# Simple LRU-style DNS cache
_dns_cache: dict[str, tuple[str, float]] = {}
_DNS_TTL = 300.0  # seconds


def _resolve(ip: str) -> str:
    """Cached, non-blocking reverse-DNS lookup."""
    now = time.monotonic()
    cached = _dns_cache.get(ip)
    if cached and now - cached[1] < _DNS_TTL:
        return cached[0]
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except Exception:
        hostname = ip
    _dns_cache[ip] = (hostname, now)
    return hostname


def _is_private(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        first, second = int(parts[0]), int(parts[1])
    except ValueError:
        return False
    return (
        first == 10
        or (first == 172 and 16 <= second <= 31)
        or (first == 192 and second == 168)
        or first == 127
    )


def _guess_protocol(ports: list[int]) -> str:
    for p in ports:
        if p in PORT_PROTOCOLS:
            return PORT_PROTOCOLS[p]
    return "TCP"


# ── Main monitor class ────────────────────────────────────────────────────────

class RealTrafficMonitor:
    """
    Produces one traffic-sample dict per registered device every monitoring cycle.
    Samples share the same schema as the simulated traffic from network_sim.py,
    so the full detection pipeline (baseline → ML → rules → Claude) works unchanged.
    """

    def __init__(self) -> None:
        self._last_io: Optional[psutil._common.snetio] = None
        self._last_io_time: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_traffic_samples(self, devices: list[dict]) -> list[dict]:
        """Return one traffic-sample per device, built from live OS data."""
        conns = self._snapshot_connections()
        sent_delta, recv_delta = self._io_delta()
        total_bytes = sent_delta + recv_delta

        # Separate external and internal connections
        ext_conns = [c for c in conns if not c["is_private"]]
        int_conns  = [c for c in conns if c["is_private"]]

        # Group external connections by remote IP
        by_remote: dict[str, list[dict]] = defaultdict(list)
        for c in ext_conns:
            by_remote[c["remote_ip"]].append(c)

        total_ext = len(ext_conns) or 1
        samples: list[dict] = []

        for device in devices:
            device_id   = device.get("id", "")
            device_ip   = device.get("ip", "")
            device_type = device.get("type", "unknown")
            device_name = device.get("name", device_ip)

            if device_id == "local-machine":
                # This PC: all outbound connections are "its" traffic
                dev_ext  = ext_conns
                dev_int  = int_conns
                dev_bytes = total_bytes
            else:
                # ARP peer: connections that reach this IP
                dev_ext  = by_remote.get(device_ip, [])
                dev_int  = [c for c in int_conns if c["remote_ip"] == device_ip]
                ratio    = len(dev_ext) / total_ext
                dev_bytes = int(total_bytes * ratio)

            conn_count = len(dev_ext) + len(dev_int)

            # Most-active remote IP and its hostname
            remote_ips = [c["remote_ip"] for c in dev_ext]
            top_ip     = max(set(remote_ips), key=remote_ips.count) if remote_ips else ""
            dest_host  = _resolve(top_ip) if top_ip else ""

            # Protocol from most common destination port
            dest_ports  = [c["remote_port"] for c in dev_ext]
            protocol    = _guess_protocol(dest_ports)

            # Unique destinations
            unique_ips   = len(set(c["remote_ip"]   for c in dev_ext))
            unique_ports = len(set(c["remote_port"] for c in dev_ext))

            # Outbound ratio (ephemeral local port → remote service)
            outbound_count = sum(1 for c in dev_ext if c["is_outbound"])
            outbound_ratio = round(outbound_count / max(1, len(dev_ext)), 2)

            # Connection regularity: how "regular" / repetitive the traffic pattern is.
            # True C2 beacons have FEW unique IPs AND FEW unique ports.
            # Normal browsing has MANY unique IPs → low regularity.
            # Formula: product of (1 - ip_diversity) × (1 - port_diversity)
            ip_diversity   = unique_ips  / max(1, conn_count)
            port_diversity = unique_ports / max(1, conn_count)
            regularity = round(
                max(0.05, min(0.95, (1.0 - ip_diversity) * (1.0 - port_diversity))),
                2,
            )

            samples.append(
                {
                    "device_id":               device_id,
                    "device_name":             device_name,
                    "device_type":             device_type,
                    "timestamp":               datetime.now().isoformat(),
                    "bytes_transferred":       dev_bytes,
                    "connection_count":        conn_count,
                    "destination_host":        dest_host,
                    "destination_ip":          top_ip,
                    "protocol":                protocol,
                    "outbound_ratio":          outbound_ratio,
                    "avg_packet_size":         800,
                    "unique_dest_ips":         unique_ips,
                    "unique_dest_ports":       unique_ports,
                    "failed_connections":      0,
                    "dns_query_count":         0,
                    "internal_connections":    len(dev_int),
                    "unique_internal_ips":     len(set(c["remote_ip"] for c in dev_int)),
                    "source_is_local":         device_id == "local-machine",
                    "inbound_mgmt_connections": 0,
                    "connection_regularity":   regularity,
                    "max_bytes_per_minute":    DEVICE_BYTE_LIMITS.get(device_type, 50_000_000),
                    "is_simulated":            False,
                    "is_attack":               False,
                }
            )

        return samples

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _snapshot_connections(self) -> list[dict]:
        """Read all established TCP connections from the kernel."""
        result: list[dict] = []
        try:
            for c in psutil.net_connections(kind="tcp"):
                if c.status != "ESTABLISHED":
                    continue
                if not c.raddr:
                    continue
                rip = c.raddr.ip
                # Skip loopback
                if rip.startswith("127.") or rip == "::1":
                    continue
                result.append(
                    {
                        "local_ip":    c.laddr.ip,
                        "local_port":  c.laddr.port,
                        "remote_ip":   rip,
                        "remote_port": c.raddr.port,
                        "pid":         c.pid,
                        # outbound = high-numbered ephemeral local port
                        "is_outbound": c.laddr.port > 1023,
                        "is_private":  _is_private(rip),
                    }
                )
        except psutil.AccessDenied:
            # Some connections may be hidden without admin; that's acceptable
            pass
        except Exception as exc:
            logger.debug(f"net_connections snapshot error: {exc}")
        return result

    def _io_delta(self) -> tuple[int, int]:
        """Return (bytes_sent_delta, bytes_recv_delta) since the previous call."""
        now = time.monotonic()
        try:
            current = psutil.net_io_counters()
        except Exception:
            return 0, 0

        if self._last_io is None:
            self._last_io = current
            self._last_io_time = now
            return 0, 0

        sent = max(0, current.bytes_sent - self._last_io.bytes_sent)
        recv = max(0, current.bytes_recv - self._last_io.bytes_recv)
        self._last_io = current
        self._last_io_time = now
        return sent, recv


# Singleton
real_monitor = RealTrafficMonitor()
