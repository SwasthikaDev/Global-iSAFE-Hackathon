"""Network status, agent control, and simulation API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agent.monitor import get_agent_status, get_all_devices, get_alerts
from agent.reasoning_core import reasoning_core
from agent.response_executor import response_executor
from agent.threat_intel import get_threat_intel
from simulation.attack_sim import (
    get_available_scenarios,
    get_active_scenario,
    start_scenario,
    stop_scenario,
    get_scenario_log,
)

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
    return {
        "actions": response_executor.get_action_log(),
        "total": len(response_executor.get_action_log()),
    }


# --- Simulation / Demo endpoints ---

@router.get("/simulation/scenarios")
async def list_scenarios():
    """List all available attack simulation scenarios."""
    return {
        "scenarios": get_available_scenarios(),
        "active_scenario": get_active_scenario(),
    }


@router.post("/simulation/start/{scenario_id}")
async def start_attack_scenario(scenario_id: str):
    """Start a simulated attack scenario for demonstration purposes."""
    result = await start_scenario(scenario_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/simulation/stop")
async def stop_attack_scenario():
    """Stop the currently running attack scenario."""
    return await stop_scenario()


@router.get("/simulation/log")
async def get_simulation_log():
    """Get the simulation event log."""
    return {
        "log": get_scenario_log(),
        "active_scenario": get_active_scenario(),
    }
