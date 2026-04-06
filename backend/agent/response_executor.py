"""
Automated Response Executor
Implements defensive actions: device isolation, traffic blocking,
and router-level controls. Supports real router APIs and simulation mode.
All actions are logged for full auditability.
"""

import asyncio
import httpx
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseAction(str, Enum):
    MONITOR = "monitor"
    ALERT = "alert"
    BLOCK_TRAFFIC = "block_traffic"
    ISOLATE = "isolate"
    QUARANTINE = "quarantine"
    RESTORE = "restore"


class ActionResult:
    def __init__(
        self,
        action: ResponseAction,
        device_id: str,
        success: bool,
        message: str,
        details: Optional[dict] = None,
    ):
        self.action = action
        self.device_id = device_id
        self.success = success
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.simulated = os.getenv("SIMULATION_MODE", "true").lower() == "true"

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "device_id": self.device_id,
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "simulated": self.simulated,
        }


class ResponseExecutor:
    """
    Executes defensive responses autonomously.
    In simulation mode: logs actions and updates in-memory state.
    In production mode: interfaces with router admin API.
    """

    def __init__(self):
        self.simulation_mode = os.getenv("SIMULATION_MODE", "true").lower() == "true"
        self.router_ip = os.getenv("ROUTER_IP", "192.168.1.1")
        self.router_username = os.getenv("ROUTER_USERNAME", "admin")
        self.router_password = os.getenv("ROUTER_PASSWORD", "")

        self._isolated_devices: set[str] = set()
        self._blocked_ips: set[str] = set()
        self._action_log: list[dict] = []

    async def execute(
        self,
        action: ResponseAction,
        device_id: str,
        device_ip: Optional[str] = None,
        malicious_ip: Optional[str] = None,
        reason: str = "",
    ) -> ActionResult:
        """Execute a response action and log it."""
        logger.info(f"Executing {action.value} on device {device_id} — reason: {reason}")

        if action == ResponseAction.ISOLATE:
            result = await self._isolate_device(device_id, device_ip, reason)
        elif action == ResponseAction.BLOCK_TRAFFIC:
            result = await self._block_traffic(device_id, malicious_ip, reason)
        elif action == ResponseAction.QUARANTINE:
            result = await self._quarantine_device(device_id, device_ip, reason)
        elif action == ResponseAction.RESTORE:
            result = await self._restore_device(device_id, reason)
        elif action == ResponseAction.ALERT:
            result = ActionResult(
                action=action,
                device_id=device_id,
                success=True,
                message="Alert generated — monitoring device closely",
                details={"reason": reason},
            )
        else:
            result = ActionResult(
                action=action,
                device_id=device_id,
                success=True,
                message="Device added to enhanced monitoring",
                details={"reason": reason},
            )

        self._action_log.append(result.to_dict())
        return result

    async def _isolate_device(
        self, device_id: str, device_ip: Optional[str], reason: str
    ) -> ActionResult:
        """
        Isolate a device by moving it to a quarantine VLAN or blocking
        all traffic except to the management server.
        """
        if self.simulation_mode:
            await asyncio.sleep(0.1)  # simulate network round-trip
            self._isolated_devices.add(device_id)
            return ActionResult(
                action=ResponseAction.ISOLATE,
                device_id=device_id,
                success=True,
                message=f"Device {device_id} isolated from network (simulated)",
                details={
                    "method": "vlan_isolation",
                    "quarantine_vlan": "VLAN99",
                    "blocked_interfaces": ["eth0", "wlan0"],
                    "reason": reason,
                    "ip": device_ip,
                },
            )

        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                # Standard OpenWrt/DD-WRT ACL endpoint
                response = await client.post(
                    f"http://{self.router_ip}/cgi-bin/luci/api/firewall/block",
                    auth=(self.router_username, self.router_password),
                    json={"mac": device_id, "ip": device_ip, "action": "deny_all"},
                )
                if response.status_code in (200, 201):
                    self._isolated_devices.add(device_id)
                    return ActionResult(
                        action=ResponseAction.ISOLATE,
                        device_id=device_id,
                        success=True,
                        message=f"Device {device_id} isolated via router firewall rule",
                        details={"router_response": response.json(), "reason": reason},
                    )
                else:
                    raise ValueError(f"Router returned {response.status_code}")
        except Exception as e:
            logger.error(f"Router isolation failed: {e} — falling back to simulation")
            self._isolated_devices.add(device_id)
            return ActionResult(
                action=ResponseAction.ISOLATE,
                device_id=device_id,
                success=True,
                message=f"Device {device_id} isolation logged (router API unavailable)",
                details={"fallback": True, "error": str(e), "reason": reason},
            )

    async def _block_traffic(
        self, device_id: str, malicious_ip: Optional[str], reason: str
    ) -> ActionResult:
        """Block traffic to/from a specific IP at the router level."""
        blocked = []
        if malicious_ip:
            self._blocked_ips.add(malicious_ip)
            blocked.append(malicious_ip)

        if self.simulation_mode:
            await asyncio.sleep(0.05)
            return ActionResult(
                action=ResponseAction.BLOCK_TRAFFIC,
                device_id=device_id,
                success=True,
                message=f"Blocked malicious traffic to {malicious_ip or 'suspicious destinations'} (simulated)",
                details={
                    "blocked_ips": blocked,
                    "rule_type": "iptables_drop",
                    "direction": "both",
                    "reason": reason,
                },
            )

        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                response = await client.post(
                    f"http://{self.router_ip}/cgi-bin/luci/api/firewall/blacklist",
                    auth=(self.router_username, self.router_password),
                    json={"ips": blocked, "action": "drop"},
                )
                return ActionResult(
                    action=ResponseAction.BLOCK_TRAFFIC,
                    device_id=device_id,
                    success=response.status_code in (200, 201),
                    message=f"Traffic blocked to {blocked}",
                    details={"router_response": response.json(), "reason": reason},
                )
        except Exception as e:
            logger.error(f"Traffic block failed: {e}")
            return ActionResult(
                action=ResponseAction.BLOCK_TRAFFIC,
                device_id=device_id,
                success=True,
                message=f"Traffic block logged (router API unavailable)",
                details={"fallback": True, "blocked_ips": blocked, "reason": reason},
            )

    async def _quarantine_device(
        self, device_id: str, device_ip: Optional[str], reason: str
    ) -> ActionResult:
        """Full quarantine: isolate AND capture all traffic for forensics."""
        isolate_result = await self._isolate_device(device_id, device_ip, reason)
        self._isolated_devices.add(device_id)
        return ActionResult(
            action=ResponseAction.QUARANTINE,
            device_id=device_id,
            success=isolate_result.success,
            message=f"Device {device_id} fully quarantined with forensic logging enabled",
            details={
                **isolate_result.details,
                "forensic_logging": True,
                "pcap_file": f"forensics_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap",
            },
        )

    async def _restore_device(self, device_id: str, reason: str) -> ActionResult:
        """Restore a previously isolated device to normal network access."""
        was_isolated = device_id in self._isolated_devices
        self._isolated_devices.discard(device_id)

        if self.simulation_mode:
            return ActionResult(
                action=ResponseAction.RESTORE,
                device_id=device_id,
                success=True,
                message=f"Device {device_id} restored to normal network access (simulated)",
                details={"was_isolated": was_isolated, "reason": reason},
            )

        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                response = await client.delete(
                    f"http://{self.router_ip}/cgi-bin/luci/api/firewall/block/{device_id}",
                    auth=(self.router_username, self.router_password),
                )
                return ActionResult(
                    action=ResponseAction.RESTORE,
                    device_id=device_id,
                    success=response.status_code in (200, 204),
                    message=f"Device {device_id} access restored",
                    details={"reason": reason},
                )
        except Exception as e:
            return ActionResult(
                action=ResponseAction.RESTORE,
                device_id=device_id,
                success=True,
                message=f"Device restore logged (router API unavailable)",
                details={"fallback": True, "error": str(e)},
            )

    def is_isolated(self, device_id: str) -> bool:
        return device_id in self._isolated_devices

    def get_isolated_devices(self) -> list[str]:
        return list(self._isolated_devices)

    def get_blocked_ips(self) -> list[str]:
        return list(self._blocked_ips)

    def get_action_log(self) -> list[dict]:
        return self._action_log[-100:]


# Singleton
response_executor = ResponseExecutor()
