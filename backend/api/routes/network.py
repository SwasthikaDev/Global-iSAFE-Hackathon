"""Network status, agent control, simulation, security-score and bandwidth APIs."""

import os

from fastapi import APIRouter, HTTPException

from agent.monitor import (
    get_agent_status,
    get_all_devices,
    get_alerts,
    get_bandwidth_history,
)
from agent.reasoning_core import reasoning_core
from agent.response_executor import response_executor
from agent.threat_intel import get_threat_intel
from agent.port_scanner import get_all_scan_results

SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() == "true"

router = APIRouter(prefix="/network", tags=["network"])


# ── Core endpoints ────────────────────────────────────────────────────────────

@router.get("/status")
async def get_network_status():
    """Overall network health: agent metrics + threat summary."""
    devices = get_all_devices()
    alerts  = get_alerts(limit=100)
    agent   = get_agent_status()
    summary = reasoning_core.get_network_summary(devices, alerts)

    return {
        "agent":           agent,
        "network_summary": summary,
        "device_count":    len(devices),
        "alert_count":     len(alerts),
        "isolated_devices": response_executor.get_isolated_devices(),
        "blocked_ips":     response_executor.get_blocked_ips(),
        "mode":            "simulation" if SIMULATION_MODE else "real",
    }


@router.get("/threat-intelligence")
async def get_threat_intel_summary():
    """Current threat intelligence feed status."""
    intel = await get_threat_intel()
    return {
        "last_updated":          intel.get("last_updated"),
        "feed_sources":          intel.get("feed_sources"),
        "malicious_ip_count":    len(intel.get("malicious_ips", {})),
        "malicious_domain_count": len(intel.get("malicious_domains", {})),
        "vulnerability_count":   len(intel.get("vulnerabilities", [])),
        "known_vulnerabilities": intel.get("vulnerabilities", []),
    }


@router.get("/action-log")
async def get_action_log():
    """Full history of autonomous actions taken by SHIELD-IoT."""
    log = response_executor.get_action_log()
    return {"actions": log, "total": len(log)}


# ── Security score ────────────────────────────────────────────────────────────

@router.get("/security-score")
async def get_security_score():
    """
    Compute a 0-100 security posture score based on real observed state:
    active threats, isolated devices, dangerous open ports, malicious IPs contacted.
    """
    devices = get_all_devices()
    alerts  = get_alerts(limit=200)
    scan_results = get_all_scan_results()

    score  = 100
    factors: list[dict] = []

    # --- Threat alerts ---
    active_alerts = [a for a in alerts if a.get("status") == "active"]
    critical = [a for a in active_alerts if a.get("severity") == "critical"]
    high     = [a for a in active_alerts if a.get("severity") == "high"]
    medium   = [a for a in active_alerts if a.get("severity") == "medium"]

    crit_deduct = min(30, len(critical) * 15)
    high_deduct = min(20, len(high) * 10)
    med_deduct  = min(10, len(medium) * 3)
    score -= crit_deduct + high_deduct + med_deduct

    if critical:
        factors.append({"name": f"{len(critical)} critical alert(s)", "deduction": -crit_deduct, "status": "fail"})
    if high:
        factors.append({"name": f"{len(high)} high alert(s)", "deduction": -high_deduct, "status": "warn"})
    if medium:
        factors.append({"name": f"{len(medium)} medium alert(s)", "deduction": -med_deduct, "status": "warn"})
    if not active_alerts:
        factors.append({"name": "No active threats detected", "deduction": 0, "status": "pass"})

    # --- Isolated devices ---
    isolated = [d for d in devices if d.get("is_isolated")]
    iso_deduct = len(isolated) * 5
    score -= iso_deduct
    if isolated:
        factors.append({"name": f"{len(isolated)} device(s) isolated", "deduction": -iso_deduct, "status": "warn"})
    else:
        factors.append({"name": "No devices isolated", "deduction": 0, "status": "pass"})

    # --- Dangerous open ports ---
    DANGEROUS_PORTS = {23: "Telnet", 21: "FTP", 7547: "TR-069", 5555: "ADB", 445: "SMB", 1883: "MQTT (unencrypted)"}
    dangerous_found: list[str] = []
    for dev_id, scan in scan_results.items():
        for port_info in scan.get("dangerous_ports", []):
            port = port_info.get("port")
            if port in DANGEROUS_PORTS:
                dangerous_found.append(f"{DANGEROUS_PORTS[port]} on {scan.get('ip', dev_id)}")

    port_deduct = min(25, len(dangerous_found) * 8)
    score -= port_deduct
    if dangerous_found:
        for item in dangerous_found[:3]:
            factors.append({"name": f"Dangerous port: {item}", "deduction": -8, "status": "fail"})
    else:
        factors.append({"name": "No dangerous open ports", "deduction": 0, "status": "pass"})

    # --- Malicious IP contacts ---
    malicious_contacts = [
        a for a in active_alerts
        if a.get("threat_intel") and a["threat_intel"].get("is_malicious")
    ]
    mal_deduct = min(30, len(malicious_contacts) * 25)
    score -= mal_deduct
    if malicious_contacts:
        factors.append({"name": f"{len(malicious_contacts)} malicious IP contact(s)", "deduction": -mal_deduct, "status": "fail"})
    else:
        factors.append({"name": "No malicious IP contacts", "deduction": 0, "status": "pass"})

    score = max(0, score)

    if score >= 90:
        grade, color = "A", "emerald"
    elif score >= 75:
        grade, color = "B", "sky"
    elif score >= 60:
        grade, color = "C", "yellow"
    elif score >= 45:
        grade, color = "D", "orange"
    else:
        grade, color = "F", "rose"

    return {
        "score":    score,
        "grade":    grade,
        "color":    color,
        "factors":  factors,
        "devices_scanned": len(scan_results),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


# ── Bandwidth history ─────────────────────────────────────────────────────────

@router.get("/bandwidth")
async def get_bandwidth():
    """Real-time upload/download bandwidth history (last ~2.5 minutes)."""
    history = get_bandwidth_history()
    if history:
        latest = history[-1]
        current_sent = latest["sent_kbps"]
        current_recv = latest["recv_kbps"]
        peak_sent = max(h["sent_kbps"] for h in history)
        peak_recv = max(h["recv_kbps"] for h in history)
    else:
        current_sent = current_recv = peak_sent = peak_recv = 0.0

    return {
        "history":       history,
        "current_sent_kbps": current_sent,
        "current_recv_kbps": current_recv,
        "peak_sent_kbps":    peak_sent,
        "peak_recv_kbps":    peak_recv,
        "mode": "simulation" if SIMULATION_MODE else "real",
    }


# ── Simulation / demo endpoints ───────────────────────────────────────────────

def _require_sim_mode():
    if not SIMULATION_MODE:
        raise HTTPException(
            status_code=400,
            detail="Attack simulation disabled (SIMULATION_MODE=false). Set SIMULATION_MODE=true in .env.",
        )


@router.get("/simulation/scenarios")
async def list_scenarios():
    if not SIMULATION_MODE:
        return {"scenarios": [], "active_scenario": None,
                "message": "Simulation disabled — running on real network data."}
    from simulation.attack_sim import get_active_scenario, get_available_scenarios
    return {"scenarios": get_available_scenarios(), "active_scenario": get_active_scenario()}


@router.post("/simulation/start/{scenario_id}")
async def start_attack_scenario(scenario_id: str):
    _require_sim_mode()
    from simulation.attack_sim import start_scenario
    result = await start_scenario(scenario_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/simulation/stop")
async def stop_attack_scenario():
    _require_sim_mode()
    from simulation.attack_sim import stop_scenario
    return await stop_scenario()


@router.get("/simulation/log")
async def get_simulation_log():
    if not SIMULATION_MODE:
        return {"log": [], "active_scenario": None,
                "message": "Simulation disabled — running on real network data."}
    from simulation.attack_sim import get_active_scenario, get_scenario_log
    return {"log": get_scenario_log(), "active_scenario": get_active_scenario()}
