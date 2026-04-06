"""Alert management API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from agent.monitor import get_alerts, dismiss_alert
from agent.reasoning_core import reasoning_core
from agent.response_executor import response_executor

router = APIRouter(prefix="/alerts", tags=["alerts"])


class DismissRequest(BaseModel):
    reason: Optional[str] = "False positive dismissed by user"


@router.get("/")
async def list_alerts(
    limit: int = Query(default=50, le=200),
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    """List all security alerts, optionally filtered by severity or status."""
    alerts = get_alerts(limit=limit, severity_filter=severity)
    if status:
        alerts = [a for a in alerts if a.get("status") == status]
    return {
        "alerts": alerts,
        "total": len(alerts),
        "critical_count": sum(1 for a in alerts if a.get("severity") == "critical"),
        "high_count": sum(1 for a in alerts if a.get("severity") == "high"),
        "medium_count": sum(1 for a in alerts if a.get("severity") == "medium"),
    }


@router.get("/summary")
async def get_alert_summary():
    """Get a statistical summary of all alerts."""
    all_alerts = get_alerts(limit=1000)
    by_severity = {}
    by_type = {}
    by_device = {}

    for alert in all_alerts:
        sev = alert.get("severity", "unknown")
        atype = alert.get("attack_type", "unknown")
        dev = alert.get("device_name", "unknown")

        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_type[atype] = by_type.get(atype, 0) + 1
        by_device[dev] = by_device.get(dev, 0) + 1

    return {
        "total_alerts": len(all_alerts),
        "by_severity": by_severity,
        "by_attack_type": by_type,
        "by_device": by_device,
        "active_alerts": sum(1 for a in all_alerts if a.get("status") == "active"),
        "isolated_devices": response_executor.get_isolated_devices(),
    }


@router.get("/{alert_id}")
async def get_alert_detail(alert_id: str):
    """Get detailed information about a specific alert including full reasoning log."""
    all_alerts = get_alerts(limit=10000)
    for alert in all_alerts:
        if alert.get("id") == alert_id:
            return {"alert": alert}
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@router.post("/{alert_id}/dismiss")
async def dismiss_alert_endpoint(alert_id: str, request: DismissRequest):
    """Dismiss an alert as a false positive."""
    success = dismiss_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {"success": True, "message": f"Alert {alert_id} dismissed", "reason": request.reason}


@router.get("/reasoning/log")
async def get_reasoning_log():
    """Get the full agent reasoning log showing decision chains."""
    return {"reasoning_log": reasoning_core.get_incident_log()}
