"""
Network Monitor — Core Agent Loop
Orchestrates the continuous observe → reason → act → explain cycle.
In simulation mode, drives the network simulator.
In production mode, consumes real passive traffic capture data.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Callable, Optional

from .anomaly_detector import anomaly_detector
from .baseline import baseline_manager
from .reasoning_core import reasoning_core
from .response_executor import ResponseAction, response_executor
from .threat_intel import check_ip, get_threat_intel

logger = logging.getLogger(__name__)

# In-memory alert store (replace with a database in production)
_alerts: list[dict] = []
_devices: dict[str, dict] = {}
_traffic_log: list[dict] = []
_agent_status = {
    "running": False,
    "cycle_count": 0,
    "last_cycle": None,
    "threats_detected": 0,
    "devices_isolated": 0,
    "start_time": None,
}

# WebSocket broadcast callback (set by the API layer)
_broadcast_callback: Optional[Callable] = None


def set_broadcast_callback(callback: Callable) -> None:
    global _broadcast_callback
    _broadcast_callback = callback


def register_device(device: dict) -> None:
    """Register a device with the monitor."""
    device_id = device["id"]
    _devices[device_id] = {
        **device,
        "status": "online",
        "threat_level": "safe",
        "last_seen": datetime.now().isoformat(),
        "is_isolated": False,
    }
    baseline_manager.get_or_create(device_id, device.get("type", "unknown"))
    logger.info(f"Registered device: {device['name']} ({device_id})")


def get_all_devices() -> list[dict]:
    return list(_devices.values())


def get_device(device_id: str) -> Optional[dict]:
    return _devices.get(device_id)


def get_alerts(limit: int = 50, severity_filter: Optional[str] = None) -> list[dict]:
    alerts = list(reversed(_alerts))
    if severity_filter:
        alerts = [a for a in alerts if a.get("severity") == severity_filter]
    return alerts[:limit]


def get_traffic_log(limit: int = 100) -> list[dict]:
    return list(reversed(_traffic_log))[:limit]


def get_agent_status() -> dict:
    return {
        **_agent_status,
        "isolated_devices": response_executor.get_isolated_devices(),
        "blocked_ips": response_executor.get_blocked_ips(),
        "total_devices": len(_devices),
        "total_alerts": len(_alerts),
    }


async def process_traffic_sample(traffic_sample: dict) -> Optional[dict]:
    """
    Process a single traffic sample through the full detection pipeline.
    Returns an incident dict if a threat is detected, else None.
    """
    device_id = traffic_sample.get("device_id", "unknown")
    destination_ip = traffic_sample.get("destination_ip", "")

    # Log traffic
    _traffic_log.append({**traffic_sample, "processed_at": datetime.now().isoformat()})
    if len(_traffic_log) > 1000:
        _traffic_log.pop(0)

    # Update device last_seen
    if device_id in _devices:
        _devices[device_id]["last_seen"] = datetime.now().isoformat()

    # Skip processing if device is already isolated
    if response_executor.is_isolated(device_id):
        return None

    device_info = _devices.get(device_id, {"id": device_id, "type": "unknown", "name": device_id})

    # Phase 1: OBSERVE — update behavioural baseline
    device_type = device_info.get("type", "unknown")
    baseline_manager.update(device_id, device_type, traffic_sample)
    baseline_score = baseline_manager.score(device_id, device_type, traffic_sample)

    # Phase 2: REASON — check threat intelligence
    threat_intel_match = None
    if destination_ip:
        threat_intel_match = await check_ip(destination_ip)

    # Force high anomaly score if destination is a known malicious IP
    if threat_intel_match and threat_intel_match.get("is_malicious"):
        baseline_score["composite_score"] = max(baseline_score["composite_score"], 0.9)
        baseline_score["is_anomalous"] = True
        baseline_score["severity"] = "critical"
        traffic_sample["threat_intel_hit"] = threat_intel_match.get("details", {})

    # Phase 3: DETECT — run anomaly detection
    detection_result = anomaly_detector.detect(traffic_sample, baseline_score)

    if not detection_result["is_threat"] and not (threat_intel_match and threat_intel_match.get("is_malicious")):
        return None

    # Phase 4: REASON (Claude) — agentic threat assessment
    reasoning = await reasoning_core.analyse_threat(
        detection_result=detection_result,
        device_info={**device_info, "network_size": len(_devices)},
        traffic_sample=traffic_sample,
        threat_intel_match=threat_intel_match,
    )

    # Phase 5: ACT — execute response
    action_str = reasoning.get("response_action", "monitor")
    try:
        action = ResponseAction(action_str)
    except ValueError:
        action = ResponseAction.ALERT

    action_result = await response_executor.execute(
        action=action,
        device_id=device_id,
        device_ip=device_info.get("ip"),
        malicious_ip=destination_ip if threat_intel_match and threat_intel_match.get("is_malicious") else None,
        reason=reasoning.get("attack_type", "anomalous behaviour"),
    )

    # Update device status
    if device_id in _devices:
        _devices[device_id]["threat_level"] = reasoning.get("severity", "low")
        _devices[device_id]["is_isolated"] = response_executor.is_isolated(device_id)
        if response_executor.is_isolated(device_id):
            _devices[device_id]["status"] = "isolated"
        elif reasoning.get("severity") in ("high", "critical"):
            _devices[device_id]["status"] = "threat"
        else:
            _devices[device_id]["status"] = "warning"

    # Phase 6: EXPLAIN — build incident report
    incident = {
        "id": f"INC-{len(_alerts) + 1:04d}",
        "timestamp": datetime.now().isoformat(),
        "device_id": device_id,
        "device_name": device_info.get("name", device_id),
        "device_type": device_type,
        "severity": reasoning.get("severity", detection_result.get("severity", "medium")),
        "attack_type": reasoning.get("attack_type", "Unknown"),
        "threat_confirmed": reasoning.get("threat_confirmed", False),
        "confidence": reasoning.get("confidence", 0.5),
        "plain_language_summary": reasoning.get("plain_language_summary", "Suspicious activity detected."),
        "technical_details": reasoning.get("technical_details", ""),
        "recommended_user_action": reasoning.get("recommended_user_action", ""),
        "response_action": action_result.action.value,
        "response_success": action_result.success,
        "response_message": action_result.message,
        "reasoning_steps": reasoning.get("reasoning_steps", []),
        "ml_score": detection_result.get("ml_score", 0),
        "baseline_score": detection_result.get("baseline_score", 0),
        "rule_matches": detection_result.get("rule_matches", []),
        "traffic_snapshot": traffic_sample,
        "threat_intel": threat_intel_match,
        "false_positive_probability": reasoning.get("false_positive_probability", 0.1),
        "status": "active",
    }

    _alerts.append(incident)
    _agent_status["threats_detected"] += 1
    if action == ResponseAction.ISOLATE:
        _agent_status["devices_isolated"] += 1

    logger.warning(
        f"INCIDENT {incident['id']}: {incident['severity'].upper()} — "
        f"{incident['attack_type']} on {incident['device_name']}"
    )

    # Broadcast to WebSocket clients
    if _broadcast_callback:
        await _broadcast_callback({"type": "incident", "data": incident})

    return incident


async def run_agent_loop(traffic_generator: Callable, interval_seconds: float = 2.0) -> None:
    """
    Main agent loop. Continuously pulls traffic samples and processes them.
    In simulation mode, uses the provided traffic generator.
    """
    _agent_status["running"] = True
    _agent_status["start_time"] = datetime.now().isoformat()
    logger.info("SHIELD-IoT agent started")

    try:
        while _agent_status["running"]:
            try:
                samples = await traffic_generator()
                for sample in samples:
                    await process_traffic_sample(sample)

                _agent_status["cycle_count"] += 1
                _agent_status["last_cycle"] = datetime.now().isoformat()

                # Broadcast status update
                if _broadcast_callback:
                    await _broadcast_callback({
                        "type": "status_update",
                        "data": get_agent_status(),
                    })

            except Exception as e:
                logger.error(f"Agent loop error: {e}", exc_info=True)

            await asyncio.sleep(interval_seconds)
    finally:
        _agent_status["running"] = False
        logger.info("SHIELD-IoT agent stopped")


def stop_agent() -> None:
    _agent_status["running"] = False


def dismiss_alert(alert_id: str) -> bool:
    for alert in _alerts:
        if alert["id"] == alert_id:
            alert["status"] = "dismissed"
            return True
    return False


def restore_device(device_id: str) -> None:
    if device_id in _devices:
        _devices[device_id]["status"] = "online"
        _devices[device_id]["threat_level"] = "safe"
        _devices[device_id]["is_isolated"] = False
