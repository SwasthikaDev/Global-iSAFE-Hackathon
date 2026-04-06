"""
Per-Device Behavioural Baseline Module
Learns and maintains a statistical profile of normal behaviour for each
device on the network. Profiles include: typical destinations, bandwidth
usage, connection frequency, active hours, and protocol distribution.
"""

import json
import logging
import math
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Predefined baselines for common IoT device types
# These represent learned "normal" patterns for each device class
DEVICE_TYPE_DEFAULTS = {
    "smart_thermostat": {
        "allowed_destinations": ["thermostat.ecobee.com", "api.nest.com", "thermostat-data.honeywell.com"],
        "max_bytes_per_minute": 5_000,
        "max_connections_per_minute": 10,
        "typical_packet_size_bytes": 300,
        "active_hours": list(range(0, 24)),
        "protocols": ["HTTPS", "MQTT"],
        "expected_outbound_ratio": 0.5,
    },
    "ip_camera": {
        "allowed_destinations": ["ring.com", "arlo.netgear.com", "nest.com", "blink.com", "reolink.com"],
        "max_bytes_per_minute": 2_000_000,
        "max_connections_per_minute": 20,
        "typical_packet_size_bytes": 1400,
        "active_hours": list(range(0, 24)),
        "protocols": ["RTSP", "HTTPS", "H264"],
        "expected_outbound_ratio": 0.85,
    },
    "smart_speaker": {
        "allowed_destinations": ["alexa.amazon.com", "api.amazon.com", "assistant.google.com", "mesu.apple.com"],
        "max_bytes_per_minute": 500_000,
        "max_connections_per_minute": 30,
        "typical_packet_size_bytes": 600,
        "active_hours": list(range(6, 24)),
        "protocols": ["HTTPS", "WSS"],
        "expected_outbound_ratio": 0.4,
    },
    "smart_plug": {
        "allowed_destinations": ["wemo.belkin.com", "tplinksmart.com", "api.smartthings.com"],
        "max_bytes_per_minute": 1_000,
        "max_connections_per_minute": 5,
        "typical_packet_size_bytes": 150,
        "active_hours": list(range(6, 23)),
        "protocols": ["HTTPS", "MQTT"],
        "expected_outbound_ratio": 0.3,
    },
    "baby_monitor": {
        "allowed_destinations": ["owlet.com", "nanit.com", "withings.com"],
        "max_bytes_per_minute": 1_500_000,
        "max_connections_per_minute": 15,
        "typical_packet_size_bytes": 1200,
        "active_hours": list(range(18, 24)) + list(range(0, 8)),
        "protocols": ["RTSP", "HTTPS", "WebRTC"],
        "expected_outbound_ratio": 0.9,
    },
    "smart_tv": {
        "allowed_destinations": ["netflix.com", "amazon.com", "youtube.com", "disneyplus.com", "hulu.com"],
        "max_bytes_per_minute": 5_000_000,
        "max_connections_per_minute": 50,
        "typical_packet_size_bytes": 1400,
        "active_hours": list(range(8, 24)),
        "protocols": ["HTTPS", "HLS", "DASH"],
        "expected_outbound_ratio": 0.1,
    },
    "router": {
        "allowed_destinations": ["8.8.8.8", "1.1.1.1", "ntp.pool.org", "dns.google"],
        "max_bytes_per_minute": 50_000_000,
        "max_connections_per_minute": 500,
        "typical_packet_size_bytes": 800,
        "active_hours": list(range(0, 24)),
        "protocols": ["DNS", "NTP", "HTTPS", "HTTP"],
        "expected_outbound_ratio": 0.5,
    },
    "unknown": {
        "allowed_destinations": [],
        "max_bytes_per_minute": 100_000,
        "max_connections_per_minute": 20,
        "typical_packet_size_bytes": 500,
        "active_hours": list(range(0, 24)),
        "protocols": ["HTTPS"],
        "expected_outbound_ratio": 0.5,
    },
}


class DeviceBaseline:
    """
    Maintains a rolling statistical baseline for a single device.
    Uses exponential moving averages for adaptive learning.
    """

    WINDOW_SIZE = 60  # number of recent observations to keep
    EMA_ALPHA = 0.1   # exponential moving average smoothing factor

    def __init__(self, device_id: str, device_type: str = "unknown"):
        self.device_id = device_id
        self.device_type = device_type
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

        defaults = DEVICE_TYPE_DEFAULTS.get(device_type, DEVICE_TYPE_DEFAULTS["unknown"])
        self.allowed_destinations: set = set(defaults["allowed_destinations"])
        self.max_bytes_per_minute: float = float(defaults["max_bytes_per_minute"])
        self.max_connections_per_minute: float = float(defaults["max_connections_per_minute"])
        self.typical_packet_size: float = float(defaults["typical_packet_size_bytes"])
        self.active_hours: set = set(defaults["active_hours"])
        self.protocols: set = set(defaults["protocols"])
        self.expected_outbound_ratio: float = defaults["expected_outbound_ratio"]

        # Rolling window for adaptive learning
        self._bytes_history: deque = deque(maxlen=self.WINDOW_SIZE)
        self._conn_history: deque = deque(maxlen=self.WINDOW_SIZE)
        self._dest_frequency: dict = defaultdict(int)

        # Learned stats
        self.learned_avg_bytes: float = self.max_bytes_per_minute * 0.3
        self.learned_avg_conns: float = self.max_connections_per_minute * 0.3
        self.is_fully_learned: bool = False
        self.observation_count: int = 0

    def update(self, traffic_sample: dict) -> None:
        """Update baseline with a new traffic observation."""
        bytes_transferred = traffic_sample.get("bytes_transferred", 0)
        connections = traffic_sample.get("connection_count", 0)
        destination = traffic_sample.get("destination_host", "")

        self._bytes_history.append(bytes_transferred)
        self._conn_history.append(connections)
        if destination:
            self._dest_frequency[destination] += 1
            # Auto-add frequently seen destinations to allowed list
            if self._dest_frequency[destination] > 10:
                self.allowed_destinations.add(destination)

        # Update EMA
        self.learned_avg_bytes = (
            self.EMA_ALPHA * bytes_transferred + (1 - self.EMA_ALPHA) * self.learned_avg_bytes
        )
        self.learned_avg_conns = (
            self.EMA_ALPHA * connections + (1 - self.EMA_ALPHA) * self.learned_avg_conns
        )

        self.observation_count += 1
        self.last_updated = datetime.now()
        if self.observation_count >= 20:
            self.is_fully_learned = True

    def compute_anomaly_score(self, traffic_sample: dict) -> dict:
        """
        Compute a per-feature anomaly score for incoming traffic.
        Returns scores between 0 (normal) and 1 (highly anomalous).
        """
        scores = {}
        details = []

        bytes_transferred = traffic_sample.get("bytes_transferred", 0)
        connections = traffic_sample.get("connection_count", 0)
        destination = traffic_sample.get("destination_host", "")
        destination_ip = traffic_sample.get("destination_ip", "")
        hour = datetime.now().hour
        protocol = traffic_sample.get("protocol", "HTTPS")
        direction = traffic_sample.get("direction", "outbound")
        packet_size = traffic_sample.get("avg_packet_size", self.typical_packet_size)

        # --- Bandwidth anomaly ---
        if self.max_bytes_per_minute > 0:
            bandwidth_ratio = bytes_transferred / self.max_bytes_per_minute
            scores["bandwidth"] = min(1.0, max(0.0, (bandwidth_ratio - 0.8) / 0.5))
            if bandwidth_ratio > 1.2:
                details.append(
                    f"Bandwidth {bytes_transferred / 1024:.1f} KB/min is "
                    f"{bandwidth_ratio:.1f}x above normal maximum"
                )

        # --- Connection frequency anomaly ---
        if self.max_connections_per_minute > 0:
            conn_ratio = connections / self.max_connections_per_minute
            scores["connection_frequency"] = min(1.0, max(0.0, (conn_ratio - 0.8) / 0.5))
            if conn_ratio > 1.5:
                details.append(
                    f"Connection count {connections} is {conn_ratio:.1f}x above normal"
                )

        # --- Destination anomaly ---
        dest_known = any(
            allowed in destination or destination in allowed
            for allowed in self.allowed_destinations
        ) if destination else True
        scores["destination"] = 0.0 if dest_known else 0.7
        if not dest_known and destination:
            details.append(f"Unusual destination: {destination} not in device whitelist")

        # --- Time-of-day anomaly ---
        scores["time_of_day"] = 0.0 if hour in self.active_hours else 0.5
        if hour not in self.active_hours and connections > 2:
            details.append(f"Device active at unusual hour: {hour:02d}:00")

        # --- Packet size anomaly ---
        if self.typical_packet_size > 0:
            size_deviation = abs(packet_size - self.typical_packet_size) / self.typical_packet_size
            scores["packet_size"] = min(1.0, size_deviation / 3.0)

        # Weighted composite score
        weights = {
            "bandwidth": 0.30,
            "connection_frequency": 0.25,
            "destination": 0.25,
            "time_of_day": 0.10,
            "packet_size": 0.10,
        }
        composite = sum(scores.get(k, 0) * w for k, w in weights.items())

        # Use a higher threshold until we have enough observations to trust the baseline.
        # This prevents noisy false positives during the learning phase.
        threshold = 0.35 if self.is_fully_learned else 0.55

        return {
            "composite_score": round(composite, 4),
            "feature_scores": scores,
            "anomaly_details": details,
            "is_anomalous": composite > threshold,
            "severity": _severity_label(composite),
        }

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "is_fully_learned": self.is_fully_learned,
            "observation_count": self.observation_count,
            "learned_avg_bytes_per_min": round(self.learned_avg_bytes, 2),
            "learned_avg_conns_per_min": round(self.learned_avg_conns, 2),
            "allowed_destinations": list(self.allowed_destinations),
            "max_bytes_per_minute": self.max_bytes_per_minute,
            "max_connections_per_minute": self.max_connections_per_minute,
            "last_updated": self.last_updated.isoformat(),
        }


class BaselineManager:
    """Manages baselines for all devices on the network."""

    def __init__(self):
        self._baselines: dict[str, DeviceBaseline] = {}

    def get_or_create(self, device_id: str, device_type: str = "unknown") -> DeviceBaseline:
        if device_id not in self._baselines:
            self._baselines[device_id] = DeviceBaseline(device_id, device_type)
            logger.info(f"Created new baseline for device {device_id} ({device_type})")
        return self._baselines[device_id]

    def update(self, device_id: str, device_type: str, traffic_sample: dict) -> None:
        baseline = self.get_or_create(device_id, device_type)
        baseline.update(traffic_sample)

    def score(self, device_id: str, device_type: str, traffic_sample: dict) -> dict:
        baseline = self.get_or_create(device_id, device_type)
        return baseline.compute_anomaly_score(traffic_sample)

    def get_all(self) -> dict[str, dict]:
        return {did: b.to_dict() for did, b in self._baselines.items()}

    def get_device(self, device_id: str) -> dict | None:
        if device_id in self._baselines:
            return self._baselines[device_id].to_dict()
        return None


def _severity_label(score: float) -> str:
    if score >= 0.75:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


# Singleton instance
baseline_manager = BaselineManager()
