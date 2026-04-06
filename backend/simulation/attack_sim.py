"""
Attack Simulation Engine
Pre-defined attack scenarios for demo purposes.
Each scenario simulates a realistic IoT attack chain that SHIELD-IoT
will detect and autonomously respond to.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from .network_sim import network_simulator

logger = logging.getLogger(__name__)

ATTACK_SCENARIOS = {
    "mirai_botnet": {
        "name": "Mirai-Style Botnet Recruitment",
        "description": (
            "Simulates a Mirai botnet attack on the baby monitor. "
            "The device begins connecting to a known C2 server with "
            "highly regular heartbeat traffic, a signature of botnet control."
        ),
        "device_id": "dev-004",
        "device_name": "Baby Monitor",
        "attack_type": "c2_communication",
        "severity": "critical",
        "phases": [
            {"duration_cycles": 3, "type": "c2_communication", "description": "Initial C2 beacon"},
            {"duration_cycles": 5, "type": "data_exfiltration", "description": "Credential harvesting"},
        ],
    },
    "camera_exfiltration": {
        "name": "IP Camera Data Exfiltration",
        "description": (
            "Simulates the Front Door Camera being compromised and "
            "streaming footage to an attacker-controlled server. "
            "Massive outbound bandwidth spike to unknown destination."
        ),
        "device_id": "dev-002",
        "device_name": "Front Door Camera",
        "attack_type": "data_exfiltration",
        "severity": "critical",
        "phases": [
            {"duration_cycles": 8, "type": "data_exfiltration", "description": "Video stream exfiltration"},
        ],
    },
    "thermostat_recon": {
        "name": "Smart Thermostat Network Reconnaissance",
        "description": (
            "Simulates a compromised thermostat performing internal network "
            "reconnaissance — scanning for vulnerable devices to spread to."
        ),
        "device_id": "dev-001",
        "device_name": "Living Room Thermostat",
        "attack_type": "port_scan",
        "severity": "high",
        "phases": [
            {"duration_cycles": 6, "type": "port_scan", "description": "Internal port scanning"},
        ],
    },
    "router_bruteforce": {
        "name": "Router SSH Brute Force Attack",
        "description": (
            "Simulates a compromised smart TV attempting to brute-force "
            "the router's SSH credentials using a credential list."
        ),
        "device_id": "dev-005",
        "device_name": "Living Room TV",
        "attack_type": "brute_force",
        "severity": "high",
        "phases": [
            {"duration_cycles": 5, "type": "brute_force", "description": "SSH credential brute force"},
        ],
    },
    "dns_tunnel": {
        "name": "Smart Speaker DNS Tunnelling",
        "description": (
            "Simulates a compromised smart speaker using DNS tunnelling "
            "to exfiltrate data and receive C2 commands covertly."
        ),
        "device_id": "dev-003",
        "device_name": "Kitchen Smart Speaker",
        "attack_type": "dns_tunnelling",
        "severity": "high",
        "phases": [
            {"duration_cycles": 7, "type": "dns_tunnelling", "description": "DNS covert channel"},
        ],
    },
}

_active_scenario: Optional[str] = None
_scenario_phase: int = 0
_scenario_cycle: int = 0
_scenario_log: list[dict] = []


def get_available_scenarios() -> list[dict]:
    return [
        {
            "id": sid,
            "name": s["name"],
            "description": s["description"],
            "device_name": s["device_name"],
            "severity": s["severity"],
        }
        for sid, s in ATTACK_SCENARIOS.items()
    ]


def get_active_scenario() -> Optional[dict]:
    if not _active_scenario:
        return None
    scenario = ATTACK_SCENARIOS.get(_active_scenario, {})
    return {
        "id": _active_scenario,
        "name": scenario.get("name"),
        "phase": _scenario_phase,
        "cycle": _scenario_cycle,
        "device_id": scenario.get("device_id"),
        "attack_type": scenario.get("attack_type"),
    }


async def start_scenario(scenario_id: str) -> dict:
    """Start an attack simulation scenario."""
    global _active_scenario, _scenario_phase, _scenario_cycle

    if scenario_id not in ATTACK_SCENARIOS:
        return {"success": False, "message": f"Unknown scenario: {scenario_id}"}

    scenario = ATTACK_SCENARIOS[scenario_id]
    _active_scenario = scenario_id
    _scenario_phase = 0
    _scenario_cycle = 0

    phase = scenario["phases"][0]
    network_simulator.inject_attack(scenario["device_id"], {"type": phase["type"]})

    event = {
        "timestamp": datetime.now().isoformat(),
        "scenario_id": scenario_id,
        "scenario_name": scenario["name"],
        "event": "started",
        "phase": phase["description"],
        "device_id": scenario["device_id"],
    }
    _scenario_log.append(event)
    logger.warning(f"Attack scenario started: {scenario['name']} on {scenario['device_name']}")

    return {
        "success": True,
        "message": f"Attack scenario '{scenario['name']}' started on {scenario['device_name']}",
        "scenario": scenario_id,
        "device_id": scenario["device_id"],
    }


async def stop_scenario() -> dict:
    """Stop the currently running attack scenario."""
    global _active_scenario

    if not _active_scenario:
        return {"success": False, "message": "No active scenario"}

    scenario = ATTACK_SCENARIOS[_active_scenario]
    network_simulator.clear_attack(scenario["device_id"])

    event = {
        "timestamp": datetime.now().isoformat(),
        "scenario_id": _active_scenario,
        "event": "stopped",
    }
    _scenario_log.append(event)
    stopped = _active_scenario
    _active_scenario = None

    return {"success": True, "message": f"Scenario {stopped} stopped", "scenario": stopped}


async def advance_scenario() -> None:
    """Called each traffic cycle to advance the scenario through its phases."""
    global _scenario_phase, _scenario_cycle

    if not _active_scenario:
        return

    scenario = ATTACK_SCENARIOS[_active_scenario]
    phases = scenario["phases"]
    current_phase = phases[_scenario_phase]

    _scenario_cycle += 1

    if _scenario_cycle >= current_phase["duration_cycles"]:
        _scenario_cycle = 0
        _scenario_phase += 1

        if _scenario_phase >= len(phases):
            # Scenario complete
            network_simulator.clear_attack(scenario["device_id"])
            event = {
                "timestamp": datetime.now().isoformat(),
                "scenario_id": _active_scenario,
                "event": "completed",
            }
            _scenario_log.append(event)
            logger.info(f"Attack scenario completed: {scenario['name']}")
            return

        next_phase = phases[_scenario_phase]
        network_simulator.inject_attack(scenario["device_id"], {"type": next_phase["type"]})
        logger.info(f"Scenario advancing to phase {_scenario_phase}: {next_phase['description']}")


def get_scenario_log() -> list[dict]:
    return _scenario_log[-50:]
