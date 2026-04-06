"""
SHIELD-IoT: Agentic AI for Autonomous Home Network Defence
Main application entry point — FastAPI server with WebSocket support.

Supports two modes:
  SIMULATION_MODE=true  — synthetic IoT traffic via network_sim.py (demo / offline)
  SIMULATION_MODE=false — real traffic from this machine via psutil + ARP discovery
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Set

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() == "true"
logger.info(f"Mode: {'SIMULATION' if SIMULATION_MODE else 'REAL DATA'}")

from agent.monitor import (
    get_agent_status,
    get_all_devices,
    register_device,
    run_agent_loop,
    set_broadcast_callback,
    stop_agent,
)
from api.routes import alerts, devices, network

if SIMULATION_MODE:
    from simulation.attack_sim import advance_scenario
    from simulation.network_sim import SIMULATED_DEVICES, network_simulator
else:
    from agent.device_discovery import discover_devices
    from agent.real_monitor import real_monitor

# WebSocket connection manager
_ws_connections: Set[WebSocket] = set()


async def broadcast(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    global _ws_connections
    if not _ws_connections:
        return
    payload = json.dumps(message, default=str)
    dead: Set[WebSocket] = set()
    for ws in _ws_connections.copy():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _ws_connections -= dead


# ── Traffic generator functions ───────────────────────────────────────────────

if SIMULATION_MODE:
    async def traffic_generator() -> list[dict]:
        await advance_scenario()
        return await network_simulator.generate_traffic()
else:
    async def traffic_generator() -> list[dict]:
        current_devices = get_all_devices()
        return await real_monitor.generate_traffic_samples(current_devices)


# ── Device refresh (real mode only) ──────────────────────────────────────────

async def _refresh_real_devices() -> None:
    """Periodically re-run ARP discovery to pick up new devices."""
    while True:
        await asyncio.sleep(60)  # re-scan every 60 s
        try:
            fresh = discover_devices()
            registered_ids = {d["id"] for d in get_all_devices()}
            for device in fresh:
                if device["id"] not in registered_ids:
                    register_device(device)
                    logger.info(f"New device found: {device['name']} ({device['ip']})")
                    if _broadcast_callback:
                        await broadcast({
                            "type": "device_added",
                            "data": {"device": device},
                        })
        except Exception as exc:
            logger.warning(f"Device refresh error: {exc}")

_broadcast_callback = broadcast  # store reference for refresh task


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting SHIELD-IoT agent...")

    if SIMULATION_MODE:
        for device in SIMULATED_DEVICES:
            register_device(device)
        logger.info(f"Simulation mode: {len(SIMULATED_DEVICES)} synthetic devices registered.")
    else:
        # Clear stale ML model so it retrains on real data
        _clear_stale_models()

        real_devices = discover_devices()
        for device in real_devices:
            register_device(device)
        logger.info(
            f"Real-data mode: {len(real_devices)} device(s) discovered and registered."
        )

    set_broadcast_callback(broadcast)

    agent_task = asyncio.create_task(
        run_agent_loop(traffic_generator, interval_seconds=2.5)
    )

    refresh_task = None
    if not SIMULATION_MODE:
        refresh_task = asyncio.create_task(_refresh_real_devices())

    yield

    logger.info("Shutting down SHIELD-IoT agent...")
    stop_agent()
    agent_task.cancel()
    if refresh_task:
        refresh_task.cancel()
    for t in [agent_task, refresh_task]:
        if t:
            try:
                await t
            except asyncio.CancelledError:
                pass


def _clear_stale_models() -> None:
    """Remove ML model files trained on simulated data so they rebuild on real traffic."""
    model_dir = os.path.join(os.path.dirname(__file__), "agent", "models")
    for fname in ("isolation_forest.joblib", "scaler.joblib"):
        path = os.path.join(model_dir, fname)
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Removed stale model file: {fname}")
            except OSError as exc:
                logger.warning(f"Could not remove {fname}: {exc}")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SHIELD-IoT",
    description="Agentic AI for Autonomous Home Network Defence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(network.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "SHIELD-IoT",
        "version": "1.0.0",
        "description": "Agentic AI for Autonomous Home Network Defence",
        "status": "operational",
        "mode": "simulation" if SIMULATION_MODE else "real",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    status = get_agent_status()
    return {
        "status": "healthy",
        "mode": "simulation" if SIMULATION_MODE else "real",
        "agent_running": status["running"],
        "timestamp": datetime.now().isoformat(),
        "uptime_cycles": status["cycle_count"],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket endpoint.
    Pushes live incident alerts, device status changes, and agent heartbeats.
    """
    await websocket.accept()
    _ws_connections.add(websocket)
    logger.info(f"WebSocket connected. Total: {len(_ws_connections)}")

    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "data": {
                        "message": "Connected to SHIELD-IoT",
                        "mode": "simulation" if SIMULATION_MODE else "real",
                        "agent_status": get_agent_status(),
                    },
                },
                default=str,
            )
        )

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps({"type": "heartbeat", "ts": datetime.now().isoformat()})
                )
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(_ws_connections)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
