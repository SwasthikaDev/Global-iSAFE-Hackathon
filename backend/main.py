"""
SHIELD-IoT: Agentic AI for Autonomous Home Network Defence
Main application entry point — FastAPI server with WebSocket support.
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

from agent.monitor import (
    register_device,
    run_agent_loop,
    stop_agent,
    set_broadcast_callback,
    get_agent_status,
)
from api.routes import alerts, devices, network
from simulation.attack_sim import advance_scenario
from simulation.network_sim import SIMULATED_DEVICES, network_simulator

# WebSocket connection manager
_ws_connections: Set[WebSocket] = set()


async def broadcast(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    global _ws_connections
    if not _ws_connections:
        return
    payload = json.dumps(message, default=str)
    dead_connections = set()
    for ws in _ws_connections.copy():
        try:
            await ws.send_text(payload)
        except Exception:
            dead_connections.add(ws)
    _ws_connections -= dead_connections


async def traffic_generator() -> list[dict]:
    """Generate traffic samples and advance attack scenarios."""
    await advance_scenario()
    return await network_simulator.generate_traffic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting SHIELD-IoT agent...")

    # Register all simulated devices
    for device in SIMULATED_DEVICES:
        register_device(device)

    # Wire up WebSocket broadcast
    set_broadcast_callback(broadcast)

    # Start the agent monitoring loop
    agent_task = asyncio.create_task(
        run_agent_loop(traffic_generator, interval_seconds=2.5)
    )

    logger.info(f"SHIELD-IoT ready. Monitoring {len(SIMULATED_DEVICES)} devices.")
    yield

    # Shutdown
    logger.info("Shutting down SHIELD-IoT agent...")
    stop_agent()
    agent_task.cancel()
    try:
        await agent_task
    except asyncio.CancelledError:
        pass


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

# Include API routers
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
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    status = get_agent_status()
    return {
        "status": "healthy",
        "agent_running": status["running"],
        "timestamp": datetime.now().isoformat(),
        "uptime_cycles": status["cycle_count"],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    Clients receive live incident alerts, status updates, and device changes.
    """
    await websocket.accept()
    _ws_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_ws_connections)}")

    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "connected",
            "data": {
                "message": "Connected to SHIELD-IoT",
                "agent_status": get_agent_status(),
            }
        }, default=str))

        # Keep alive and handle incoming messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "heartbeat", "ts": datetime.now().isoformat()}))
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_ws_connections)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
