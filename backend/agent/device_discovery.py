"""
Real Network Device Discovery
Discovers devices on the local network using the ARP cache and local interface info.
Resolves hostnames and maps MAC OUI prefixes to vendor names for richer device context.
"""

import logging
import re
import socket
import subprocess
from datetime import datetime

import psutil

logger = logging.getLogger(__name__)

# Known OUI vendor prefix → vendor name (first 3 bytes of MAC, colon-separated, uppercase)
OUI_VENDORS = {
    "00:50:56": "VMware",
    "00:0C:29": "VMware",
    "00:1A:11": "Google",
    "3C:5A:B4": "Google",
    "AC:84:C6": "ASUSTeK",
    "B0:6E:BF": "ASUSTeK",
    "C8:7F:54": "ASUSTeK",
    "44:67:47": "Belkin",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Foundation",
    "E4:5F:01": "Raspberry Pi Foundation",
    "D8:3A:DD": "Raspberry Pi Foundation",
    "00:17:88": "Philips Hue",
    "EC:B5:FA": "Philips Hue",
    "18:B4:30": "Nest Labs",
    "64:16:66": "Nest Labs",
    "18:FE:34": "Espressif (IoT)",
    "24:6F:28": "Espressif (IoT)",
    "30:AE:A4": "Espressif (IoT)",
    "A4:CF:12": "Espressif (IoT)",
    "60:01:94": "TP-Link",
    "50:C7:BF": "TP-Link",
    "1C:3B:F3": "TP-Link",
    "30:DE:4B": "TP-Link",
    "54:AF:97": "TP-Link",
    "38:10:D5": "Amazon",
    "74:75:48": "Amazon Echo",
    "18:74:2E": "Amazon",
    "FC:A6:67": "Amazon",
    "B4:E6:2D": "Apple",
    "F8:FF:C2": "Apple",
    "AC:63:BE": "Apple",
    "A4:C3:F0": "Apple",
    "3C:22:FB": "Apple",
    "FC:64:BA": "Samsung",
    "D0:03:4B": "Samsung",
    "84:D6:D0": "Samsung",
    "8C:71:F8": "Samsung",
    "CC:32:E5": "Samsung",
    "00:E0:4C": "Realtek",
    "DC:EF:CA": "Netgear (Arlo)",
    "A0:40:A0": "Netgear",
    "68:37:E9": "Amazon Echo",
    "FC:65:DE": "Ring (Amazon)",
    "78:8A:20": "Ring (Amazon)",
    "94:65:2D": "Wyze Labs",
    "2C:AA:8E": "Wyze Labs",
}


def _oui_lookup(mac: str) -> str:
    """Return vendor name from MAC OUI prefix, or empty string if unknown."""
    prefix = mac.upper().replace("-", ":")[:8]
    return OUI_VENDORS.get(prefix, "")


def _device_type_from_context(vendor: str, hostname: str, ip: str) -> str:
    """Infer device type from vendor name, hostname, and IP."""
    vl = vendor.lower()
    hl = hostname.lower()

    if ip.endswith(".1") or ip.endswith(".254"):
        return "router"

    if any(x in vl for x in ["raspberry pi", "espressif"]):
        return "iot_controller"
    if any(x in vl for x in ["philips hue", "nest", "ring", "arlo", "wyze"]):
        return "smart_home"
    if any(x in vl for x in ["amazon echo"]):
        return "smart_speaker"
    if "apple" in vl:
        return "mobile"
    if "samsung" in vl:
        return "smart_tv"
    if any(x in vl for x in ["asustek", "asus", "tp-link", "netgear", "linksys", "belkin", "cisco"]):
        return "router"

    if any(x in hl for x in ["iphone", "ipad", "android", "phone", "mobile"]):
        return "mobile"
    if any(x in hl for x in ["tv", "firetv", "chromecast", "roku", "shield"]):
        return "smart_tv"
    if any(x in hl for x in ["router", "gateway", "modem", "ap-"]):
        return "router"
    if any(x in hl for x in ["camera", "cam", "doorbell", "ring", "arlo", "wyze"]):
        return "ip_camera"
    if any(x in hl for x in ["echo", "alexa", "homepod", "speaker"]):
        return "smart_speaker"
    if any(x in hl for x in ["thermostat", "nest", "ecobee"]):
        return "smart_thermostat"
    if any(x in hl for x in ["printer", "print"]):
        return "printer"

    return "unknown"


def _get_local_ip() -> str:
    """Get the primary outbound IP of this machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _get_local_mac(local_ip: str) -> str:
    """Get the MAC address of the interface that holds the given IP."""
    try:
        for _iface, addrs in psutil.net_if_addrs().items():
            ips_on_iface = [a.address for a in addrs if a.family == socket.AF_INET]
            if local_ip in ips_on_iface:
                for a in addrs:
                    if a.family == psutil.AF_LINK and a.address not in ("", "00:00:00:00:00:00"):
                        return a.address.upper()
    except Exception:
        pass
    return "00:00:00:00:00:00"


def _parse_arp_table(exclude_ip: str) -> list[dict]:
    """Parse the OS ARP table to discover LAN peers."""
    peers = []
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            # Windows ARP format:  "  192.168.1.1    00-11-22-33-44-55    dynamic"
            m = re.match(
                r"\s+(\d+\.\d+\.\d+\.\d+)\s+([\da-fA-F][\da-fA-F\-:]{14,})\s+(\w+)",
                line,
            )
            if not m:
                continue
            ip, mac, entry_type = m.groups()

            if ip == exclude_ip:
                continue

            # Skip broadcast, multicast (224.x–239.x), link-local, and incomplete entries
            mac_norm = mac.upper().replace("-", ":")
            if (
                ip.endswith(".255")
                or mac_norm in ("FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00")
                or ip.startswith("224.")
                or ip.startswith("225.") or ip.startswith("226.") or ip.startswith("227.")
                or ip.startswith("228.") or ip.startswith("229.") or ip.startswith("230.")
                or ip.startswith("231.") or ip.startswith("232.") or ip.startswith("233.")
                or ip.startswith("234.") or ip.startswith("235.") or ip.startswith("236.")
                or ip.startswith("237.") or ip.startswith("238.") or ip.startswith("239.")
                or ip.startswith("169.254.")
            ):
                continue

            vendor = _oui_lookup(mac_norm) or "Unknown Vendor"

            # Attempt reverse DNS (quick, non-blocking)
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = ip

            dev_type = _device_type_from_context(vendor, hostname, ip)

            # Build a readable display name
            parts: list[str] = []
            if vendor and vendor != "Unknown Vendor":
                parts.append(vendor)
            if hostname != ip:
                parts.append(hostname)
            display_name = " — ".join(parts) if parts else f"Network Device [{ip}]"

            peers.append(
                {
                    "id": f"arp-{ip.replace('.', '-')}",
                    "name": display_name,
                    "type": dev_type,
                    "manufacturer": vendor,
                    "ip": ip,
                    "mac": mac_norm,
                    "model": f"{vendor} Device",
                    "firmware": "N/A",
                    "discovered_at": datetime.now().isoformat(),
                }
            )
    except Exception as exc:
        logger.warning(f"ARP table parse error: {exc}")
    return peers


def discover_devices() -> list[dict]:
    """
    Returns a list of device dicts ready for monitor.register_device().
    Always includes this machine plus every peer visible in the ARP cache.
    """
    local_ip = _get_local_ip()
    hostname = socket.gethostname()

    devices: list[dict] = [
        {
            "id": "local-machine",
            "name": f"{hostname} (This Computer)",
            "type": "workstation",
            "manufacturer": "Local",
            "ip": local_ip,
            "mac": _get_local_mac(local_ip),
            "model": "Windows Workstation",
            "firmware": "N/A",
        }
    ]

    arp_devices = _parse_arp_table(exclude_ip=local_ip)
    seen_ips = {local_ip}
    for d in arp_devices:
        if d["ip"] not in seen_ips:
            seen_ips.add(d["ip"])
            devices.append(d)

    logger.info(
        f"Device discovery complete: {len(devices)} device(s) found "
        f"({len(arp_devices)} ARP peers + local machine)"
    )
    return devices
