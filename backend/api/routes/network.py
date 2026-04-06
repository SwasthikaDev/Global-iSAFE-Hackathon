"""Network status, agent control, and simulation API routes."""

import os

from fastapi import APIRouter, HTTPException

from agent.monitor import get_agent_status, get_all_devices, get_alerts
from agent.reasoning_core import reasoning_core
from agent.response_executor import response_executor
from agent.threat_intel import get_threat_intel

SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() == "true"

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/status")
async def get_network_status():
    """Get overall network health status and agent metrics."""
    devices = get_all_devices()
    alerts = get_alerts(limit=100)
    agent_status = get_agent_status()
    summary = reasoning_core.get_network_summary(devices, alerts)

    return {
        "agent": agent_status,
        "network_summary": summary,
        "device_count": len(devices),
        "alert_count": len(alerts),
        "isolated_devices": response_executor.get_isolated_devices(),
        "blocked_ips": response_executor.get_blocked_ips(),
        "mode": "simulation" if SIMULATION_MODE else "real",
    }


@router.get("/threat-intelligence")
async def get_threat_intel_summary():
    """Get current threat intelligence feed status."""
    intel = await get_threat_intel()
    return {
        "last_updated": intel.get("last_updated"),
        "feed_sources": intel.get("feed_sources"),
        "malicious_ip_count": len(intel.get("malicious_ips", {})),
        "malicious_domain_count": len(intel.get("malicious_domains", {})),
        "vulnerability_count": len(intel.get("vulnerabilities", [])),
        "known_vulnerabilities": intel.get("vulnerabilities", []),
    }


@router.get("/action-log")
async def get_action_log():
    """Get the full history of autonomous actions taken by SHIELD-IoT."""
    log = response_executor.get_action_log()
    return {
        "actions": log,
        "total": len(log),
    }


# ── Simulation / Demo endpoints ───────────────────────────────────────────────
# In real-data mode these endpoints return a 400 to make the behaviour explicit.

def _require_sim_mode():
    if not SIMULATION_MODE:
        raise HTTPException(
            status_code=400,
            detail=(
                "Attack simulation is disabled in real-data mode "
                "(SIMULATION_MODE=false). Set SIMULATION_MODE=true in .env to "
                "use synthetic attack scenarios."
            ),
        )


@router.get("/simulation/scenarios")
async def list_scenarios():
    """List all available attack simulation scenarios."""
    if not SIMULATION_MODE:
        return {
            "scenarios": [],
            "active_scenario": None,
            "message": "Simulation disabled — running on real network data.",
        }
    from simulation.attack_sim import get_active_scenario, get_available_scenarios
    return {
        "scenarios": get_available_scenarios(),
        "active_scenario": get_active_scenario(),
    }


@router.post("/simulation/start/{scenario_id}")
async def start_attack_scenario(scenario_id: str):
    """Start a simulated attack scenario for demonstration purposes."""
    _require_sim_mode()
    from simulation.attack_sim import start_scenario
    result = await start_scenario(scenario_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/simulation/stop")
async def stop_attack_scenario():
    """Stop the currently running attack scenario."""
    _require_sim_mode()
    from simulation.attack_sim import stop_scenario
    return await stop_scenario()


@router.get("/simulation/log")
async def get_simulation_log():
    """Get the simulation event log."""
    if not SIMULATION_MODE:
        return {
            "log": [],
            "active_scenario": None,
            "message": "Simulation disabled — running on real network data.",
        }
    from simulation.attack_sim import get_active_scenario, get_scenario_log
    return {
        "log": get_scenario_log(),
        "active_scenario": get_active_scenario(),
    }
