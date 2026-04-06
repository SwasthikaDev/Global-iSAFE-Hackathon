"""Device management API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agent.monitor import (
    get_all_devices,
    get_device,
    restore_device,
    get_traffic_log,
)
from agent.baseline import baseline_manager
from agent.response_executor import ResponseAction, response_executor
from agent.port_scanner import get_scan_result, get_all_scan_results

router = APIRouter(prefix="/devices", tags=["devices"])


class RestoreRequest(BaseModel):
    reason: Optional[str] = "Manual restore by user"


@router.get("/")
async def list_devices():
    """List all known devices with status and latest port scan results."""
    devices = get_all_devices()
    isolated = set(response_executor.get_isolated_devices())
    for device in devices:
        device["is_isolated"] = device["id"] in isolated
        scan = get_scan_result(device["id"])
        device["port_scan"] = {
            "risk_level":      scan["risk_level"]   if scan else "unknown",
            "open_port_count": scan["total_open"]   if scan else None,
            "dangerous_ports": scan["dangerous_ports"] if scan else [],
            "scan_time":       scan["scan_time"]    if scan else None,
        }
    return {"devices": devices, "total": len(devices)}


@router.get("/{device_id}")
async def get_device_detail(device_id: str):
    """Get detailed information about a specific device."""
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    baseline = baseline_manager.get_device(device_id)
    return {
        "device": device,
        "baseline": baseline,
        "is_isolated": response_executor.is_isolated(device_id),
    }


@router.post("/{device_id}/restore")
async def restore_device_endpoint(device_id: str, request: RestoreRequest):
    """Restore an isolated device to normal network access."""
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

    result = await response_executor.execute(
        action=ResponseAction.RESTORE,
        device_id=device_id,
        reason=request.reason or "Manual restore",
    )
    restore_device(device_id)
    return {"success": result.success, "message": result.message, "action": result.to_dict()}


@router.get("/{device_id}/traffic")
async def get_device_traffic(device_id: str, limit: int = 50):
    """Get recent traffic samples for a specific device."""
    all_traffic = get_traffic_log(limit=500)
    device_traffic = [t for t in all_traffic if t.get("device_id") == device_id]
    return {"device_id": device_id, "traffic": device_traffic[:limit], "total": len(device_traffic)}


@router.get("/{device_id}/baseline")
async def get_device_baseline(device_id: str):
    """Get the learned behavioural baseline for a device."""
    baseline = baseline_manager.get_device(device_id)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"No baseline found for device {device_id}")
    return {"device_id": device_id, "baseline": baseline}


@router.get("/{device_id}/ports")
async def get_device_ports(device_id: str):
    """Get the most recent port scan result for a device."""
    result = get_scan_result(device_id)
    if not result:
        return {
            "device_id": device_id,
            "open_ports": [],
            "dangerous_ports": [],
            "risk_level": "unknown",
            "scan_time": None,
            "message": "No port scan results yet — scan runs on startup and every 5 minutes.",
        }
    return result


