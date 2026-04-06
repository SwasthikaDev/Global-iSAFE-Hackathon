"""
Realistic IoT Home Network Simulator
Generates synthetic traffic data mimicking a real smart home with 8–12 devices.
Traffic patterns are based on published IoT traffic datasets (UNSW-NB15, N-BaIoT).
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Callable, Optional

# Simulated home network topology
SIMULATED_DEVICES = [
    {
        "id": "dev-001",
        "name": "Living Room Thermostat",
        "type": "smart_thermostat",
        "manufacturer": "Ecobee",
        "ip": "192.168.1.10",
        "mac": "A4:C3:F0:11:22:33",
        "model": "SmartThermostat Premium",
        "firmware": "4.8.7.132",
    },
    {
        "id": "dev-002",
        "name": "Front Door Camera",
        "type": "ip_camera",
        "manufacturer": "Ring",
        "ip": "192.168.1.11",
        "mac": "FC:65:DE:11:22:44",
        "model": "Video Doorbell Pro 2",
        "firmware": "3.3.72",
    },
    {
        "id": "dev-003",
        "name": "Kitchen Smart Speaker",
        "type": "smart_speaker",
        "manufacturer": "Amazon",
        "ip": "192.168.1.12",
        "mac": "68:37:E9:11:22:55",
        "model": "Echo Dot (5th Gen)",
        "firmware": "7.2.4.0",
    },
    {
        "id": "dev-004",
        "name": "Baby Monitor",
        "type": "baby_monitor",
        "manufacturer": "Nanit",
        "ip": "192.168.1.13",
        "mac": "50:C7:BF:11:22:66",
        "model": "Nanit Pro",
        "firmware": "2.11.0",
    },
    {
        "id": "dev-005",
        "name": "Living Room TV",
        "type": "smart_tv",
        "manufacturer": "Samsung",
        "ip": "192.168.1.14",
        "mac": "8C:71:F8:11:22:77",
        "model": "QLED 65",
        "firmware": "1450.3",
    },
    {
        "id": "dev-006",
        "name": "Smart Plug (Bedroom Lamp)",
        "type": "smart_plug",
        "manufacturer": "TP-Link",
        "ip": "192.168.1.15",
        "mac": "50:C7:BF:11:33:88",
        "model": "Kasa EP25",
        "firmware": "1.0.15",
    },
    {
        "id": "dev-007",
        "name": "Home Router",
        "type": "router",
        "manufacturer": "ASUS",
        "ip": "192.168.1.1",
        "mac": "AC:84:C6:11:22:99",
        "model": "RT-AX88U",
        "firmware": "3.0.0.4.388",
    },
    {
        "id": "dev-008",
        "name": "Backyard Camera",
        "type": "ip_camera",
        "manufacturer": "Arlo",
        "ip": "192.168.1.16",
        "mac": "DC:EF:CA:11:22:AA",
        "model": "Pro 4",
        "firmware": "1.130.17.0",
    },
]

# Normal traffic profiles per device type (bytes/min, connections/min)
NORMAL_TRAFFIC = {
    "smart_thermostat": {
        "bytes_range": (200, 2_000),
        "conn_range": (1, 5),
        "destinations": ["thermostat.ecobee.com", "api.ecobee.com"],
        "destination_ips": ["52.204.103.47", "54.87.231.43"],
        "protocols": ["HTTPS", "MQTT"],
        "outbound_ratio": (0.4, 0.6),
        "avg_packet_size": (200, 400),
    },
    "ip_camera": {
        "bytes_range": (100_000, 800_000),
        "conn_range": (2, 8),
        "destinations": ["ring.com", "live.ring.com", "arlo.netgear.com"],
        "destination_ips": ["54.239.28.85", "204.246.172.50"],
        "protocols": ["RTSP", "HTTPS"],
        "outbound_ratio": (0.75, 0.95),
        "avg_packet_size": (1100, 1400),
    },
    "smart_speaker": {
        "bytes_range": (5_000, 200_000),
        "conn_range": (5, 20),
        "destinations": ["alexa.amazon.com", "api.amazon.com", "avs-alexa-na.amazon.com"],
        "destination_ips": ["54.239.28.85", "52.94.236.248"],
        "protocols": ["HTTPS", "WSS"],
        "outbound_ratio": (0.3, 0.5),
        "avg_packet_size": (400, 800),
    },
    "baby_monitor": {
        "bytes_range": (50_000, 1_000_000),
        "conn_range": (2, 6),
        "destinations": ["stream.nanit.com", "api.nanit.com"],
        "destination_ips": ["34.195.162.12", "52.23.167.89"],
        "protocols": ["RTSP", "HTTPS", "WebRTC"],
        "outbound_ratio": (0.8, 0.95),
        "avg_packet_size": (1000, 1400),
    },
    "smart_tv": {
        "bytes_range": (500_000, 4_000_000),
        "conn_range": (10, 40),
        "destinations": ["netflix.com", "api.netflix.com", "youtube.com"],
        "destination_ips": ["52.94.236.248", "108.175.32.157"],
        "protocols": ["HTTPS", "HLS"],
        "outbound_ratio": (0.05, 0.20),
        "avg_packet_size": (1300, 1500),
    },
    "smart_plug": {
        "bytes_range": (50, 500),
        "conn_range": (1, 3),
        "destinations": ["tplinksmart.com", "devs.tplinkcloud.com"],
        "destination_ips": ["54.213.170.37", "52.43.109.53"],
        "protocols": ["HTTPS", "MQTT"],
        "outbound_ratio": (0.25, 0.45),
        "avg_packet_size": (100, 200),
    },
    "router": {
        "bytes_range": (10_000, 200_000),
        "conn_range": (20, 100),
        "destinations": ["8.8.8.8", "1.1.1.1", "ntp.pool.org"],
        "destination_ips": ["8.8.8.8", "1.1.1.1"],
        "protocols": ["DNS", "NTP", "HTTPS"],
        "outbound_ratio": (0.4, 0.6),
        "avg_packet_size": (400, 900),
    },
    "unknown": {
        "bytes_range": (1_000, 50_000),
        "conn_range": (2, 15),
        "destinations": ["unknown.host"],
        "destination_ips": ["0.0.0.0"],
        "protocols": ["HTTPS"],
        "outbound_ratio": (0.4, 0.6),
        "avg_packet_size": (400, 700),
    },
}


class NetworkSimulator:
    """
    Simulates IoT home network traffic.
    Generates normal traffic with occasional noise to train the baseline.
    Attack scenarios are injected separately via attack_sim.py.
    """

    def __init__(self):
        self.devices = SIMULATED_DEVICES.copy()
        self._attack_active: dict[str, dict] = {}  # device_id -> attack config
        self._cycle = 0

    def inject_attack(self, device_id: str, attack_config: dict) -> None:
        """Inject a simulated attack on a specific device."""
        self._attack_active[device_id] = {**attack_config, "injected_at": time.time()}

    def clear_attack(self, device_id: str) -> None:
        self._attack_active.pop(device_id, None)

    def clear_all_attacks(self) -> None:
        self._attack_active.clear()

    async def generate_traffic(self) -> list[dict]:
        """Generate one cycle of traffic samples for all devices."""
        samples = []
        self._cycle += 1
        now = datetime.now()

        for device in self.devices:
            device_id = device["id"]
            device_type = device["type"]
            profile = NORMAL_TRAFFIC.get(device_type, NORMAL_TRAFFIC["unknown"])

            # Check if this device has an active attack
            if device_id in self._attack_active:
                attack = self._attack_active[device_id]
                sample = self._generate_attack_traffic(device, attack, profile)
            else:
                sample = self._generate_normal_traffic(device, profile, now)

            samples.append(sample)

        return samples

    def _generate_normal_traffic(self, device: dict, profile: dict, now: datetime) -> dict:
        """Generate realistic normal traffic for a device."""
        hour = now.hour

        # Reduce activity during sleep hours for certain device types
        activity_multiplier = 1.0
        if device["type"] in ("smart_tv", "smart_speaker") and hour in range(0, 6):
            activity_multiplier = 0.1
        elif device["type"] == "smart_plug" and hour in range(2, 6):
            activity_multiplier = 0.2

        bytes_min, bytes_max = profile["bytes_range"]
        conn_min, conn_max = profile["conn_range"]

        bytes_transferred = int(random.uniform(bytes_min, bytes_max) * activity_multiplier)
        conn_count = max(0, int(random.gauss(
            (conn_min + conn_max) / 2 * activity_multiplier,
            (conn_max - conn_min) / 6
        )))

        dest_idx = random.randint(0, len(profile["destinations"]) - 1)
        dest_host = profile["destinations"][dest_idx]
        dest_ip = profile["destination_ips"][min(dest_idx, len(profile["destination_ips"]) - 1)]

        out_min, out_max = profile["outbound_ratio"]
        pkt_min, pkt_max = profile["avg_packet_size"]

        return {
            "device_id": device["id"],
            "device_name": device["name"],
            "device_type": device["type"],
            "timestamp": datetime.now().isoformat(),
            "bytes_transferred": bytes_transferred,
            "connection_count": conn_count,
            "destination_host": dest_host,
            "destination_ip": dest_ip,
            "protocol": random.choice(profile["protocols"]),
            "outbound_ratio": round(random.uniform(out_min, out_max), 2),
            "avg_packet_size": random.randint(pkt_min, pkt_max),
            "unique_dest_ips": random.randint(1, 3),
            "unique_dest_ports": random.randint(1, 4),
            "failed_connections": random.randint(0, 1),
            "dns_query_count": random.randint(0, 5),
            "internal_connections": random.randint(0, 2),
            "unique_internal_ips": random.randint(0, 1),
            "source_is_local": True,
            "inbound_mgmt_connections": 0,
            "connection_regularity": round(random.uniform(0.1, 0.4), 2),
            # Include the normal max so rule conditions can compare against it correctly.
            "max_bytes_per_minute": profile["bytes_range"][1],
            "is_simulated": True,
            "is_attack": False,
        }

    def _generate_attack_traffic(
        self, device: dict, attack: dict, normal_profile: dict
    ) -> dict:
        """Generate attack traffic pattern for a device."""
        attack_type = attack.get("type", "c2_communication")
        base = self._generate_normal_traffic(device, normal_profile, datetime.now())

        if attack_type == "c2_communication":
            base.update({
                "bytes_transferred": random.randint(5_000, 20_000),
                "connection_count": random.randint(25, 50),
                "destination_host": "malicious-iot-c2.ru",
                "destination_ip": "10.0.0.99",
                "protocol": "TCP",
                "outbound_ratio": 0.95,
                "connection_regularity": round(random.uniform(0.90, 0.99), 2),
                "unique_dest_ips": 1,
                "unique_dest_ports": 1,
                "is_attack": True,
                "attack_type": "c2_communication",
            })
        elif attack_type == "data_exfiltration":
            normal_bytes = normal_profile["bytes_range"][1]
            base.update({
                "bytes_transferred": normal_bytes * random.randint(8, 20),
                "connection_count": random.randint(5, 15),
                "destination_host": "exfil-data.xyz",
                "destination_ip": "10.0.0.100",
                "protocol": "HTTPS",
                "outbound_ratio": 0.98,
                "unique_dest_ips": 1,
                "is_attack": True,
                "attack_type": "data_exfiltration",
            })
        elif attack_type == "port_scan":
            base.update({
                "bytes_transferred": random.randint(50_000, 200_000),
                "connection_count": random.randint(80, 200),
                "destination_host": "192.168.1.0/24",
                "destination_ip": "192.168.1.50",
                "protocol": "TCP",
                "outbound_ratio": 0.99,
                "unique_dest_ips": random.randint(20, 50),
                "unique_dest_ports": random.randint(30, 100),
                "failed_connections": random.randint(50, 150),
                "internal_connections": random.randint(30, 80),
                "unique_internal_ips": random.randint(10, 30),
                "is_attack": True,
                "attack_type": "port_scan",
            })
        elif attack_type == "brute_force":
            base.update({
                "bytes_transferred": random.randint(10_000, 50_000),
                "connection_count": random.randint(100, 300),
                "destination_ip": "192.168.1.1",
                "protocol": "SSH",
                "failed_connections": random.randint(80, 200),
                "dest_ports": [22, 23, 80, 443],
                "unique_dest_ports": 4,
                "is_attack": True,
                "attack_type": "brute_force",
            })
        elif attack_type == "dns_tunnelling":
            base.update({
                "bytes_transferred": random.randint(5_000, 30_000),
                "connection_count": random.randint(50, 150),
                "destination_host": "botnet-update.cn",
                "destination_ip": "91.92.109.51",
                "protocol": "DNS",
                "dns_query_count": random.randint(150, 400),
                "avg_dns_payload_size": random.randint(180, 350),
                "unique_dest_ips": 2,
                "is_attack": True,
                "attack_type": "dns_tunnelling",
            })

        base["max_bytes_per_minute"] = normal_profile["bytes_range"][1]
        return base


# Singleton
network_simulator = NetworkSimulator()
