# SHIELD-IoT 🛡️
### Agentic AI for Autonomous Home Network Defence

> **iSAFE Hackathon 2026 — Track 2: Defend the Digital Citizen**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com)
[![Claude API](https://img.shields.io/badge/Claude-API-orange.svg)](https://anthropic.com)

---

## The Problem

The average household has 10–15 smart IoT devices — cameras, baby monitors, smart speakers, thermostats — each running lightweight firmware with minimal security. AI-driven IoT attacks surged 54% in 2026. Autonomous malware now compromises a device in under 60 seconds.

**The citizen has no defence.** Intrusion detection systems require deep expertise and cost thousands. Nothing equivalent exists for ordinary people.

## The Solution

SHIELD-IoT is an **agentic AI system** that autonomously monitors, detects, and neutralises cyber threats targeting smart devices on a home network — with **zero technical knowledge required** from the user.

### How It Works — Four Continuous Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHIELD-IoT Agent Loop                        │
│                                                                  │
│  1. OBSERVE ──► 2. REASON ──► 3. ACT ──► 4. EXPLAIN            │
│                                                                  │
│  Passive traffic    Claude API       Isolate device    Plain     │
│  monitoring +       threat           Block traffic     language  │
│  per-device         assessment       Log forensics     alert     │
│  baseline                                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com) (optional — falls back to rule-based reasoning)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
python main.py
```

The API server starts at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Dashboard opens at `http://localhost:5173`.

### Running a Demo

1. Start the backend — it immediately begins simulating 8 IoT devices
2. Start the frontend and open the dashboard
3. In the **Attack Simulation** panel, click **Run** on any scenario
4. Watch SHIELD-IoT detect the attack, reason about it, and autonomously isolate the device
5. Expand any alert to see the full **Agent Reasoning Chain**

---

## Architecture

```
shield-iot/
├── backend/
│   ├── main.py                    # FastAPI server + WebSocket
│   ├── agent/
│   │   ├── monitor.py             # Core observe→reason→act→explain loop
│   │   ├── baseline.py            # Per-device behavioural baseline (EMA)
│   │   ├── anomaly_detector.py    # Isolation Forest + rule-based detection
│   │   ├── reasoning_core.py      # Claude API agentic reasoning
│   │   ├── response_executor.py   # Autonomous response (isolate/block)
│   │   └── threat_intel.py        # Live threat intelligence feeds
│   ├── api/routes/
│   │   ├── devices.py             # Device management endpoints
│   │   ├── alerts.py              # Alert management endpoints
│   │   └── network.py             # Network status + simulation
│   └── simulation/
│       ├── network_sim.py         # Realistic IoT traffic simulation
│       └── attack_sim.py          # Attack scenario engine
└── frontend/
    └── src/
        ├── App.tsx                # Main dashboard
        ├── components/            # UI components
        └── hooks/useWebSocket.ts  # Real-time WebSocket connection
```

### Technical Stack

| Component | Technology |
|-----------|-----------|
| Agentic Reasoning | Claude API (claude-opus-4-5) |
| Anomaly Detection | Isolation Forest (scikit-learn) |
| Behavioural Baseline | Exponential Moving Average per device |
| Backend API | FastAPI + WebSockets |
| Traffic Monitoring | Passive metadata analysis (no payload) |
| Threat Intelligence | AbuseIPDB, built-in IOC list |
| Frontend Dashboard | React 18 + TypeScript + Tailwind CSS |
| Charts | Recharts |
| Attack Response | Router API (OpenWrt/DD-WRT compatible) |

---

## Attack Scenarios (Demo)

| Scenario | Target Device | Attack Type | What SHIELD Does |
|----------|--------------|-------------|-----------------|
| Mirai Botnet Recruitment | Baby Monitor | C2 beacon + exfil | Isolates device, blocks C2 IP |
| IP Camera Exfiltration | Front Door Camera | Data exfiltration | Quarantines, logs forensics |
| Network Reconnaissance | Smart Thermostat | Port scanning | Blocks internal scans |
| Router Brute Force | Smart TV | SSH brute force | Blocks attack traffic |
| DNS Tunnelling | Smart Speaker | Covert C2 channel | Isolates, generates report |

---

## API Reference

### Key Endpoints

```
GET  /api/devices/              List all network devices
GET  /api/devices/{id}          Device detail + baseline
POST /api/devices/{id}/restore  Restore isolated device

GET  /api/alerts/               List all security alerts
GET  /api/alerts/{id}           Alert detail + reasoning chain
POST /api/alerts/{id}/dismiss   Dismiss false positive
GET  /api/alerts/reasoning/log  Full agent reasoning log

GET  /api/network/status        Network health + agent metrics
GET  /api/network/action-log    Autonomous action history
GET  /api/network/threat-intelligence  Threat feed status

POST /api/network/simulation/start/{id}  Start attack scenario
POST /api/network/simulation/stop        Stop active scenario
```

Full OpenAPI spec: `http://localhost:8000/docs`

### WebSocket — Real-Time Events

Connect to `ws://localhost:8000/ws` to receive:

```json
{ "type": "incident", "data": { ... alert object ... } }
{ "type": "status_update", "data": { ... agent status ... } }
{ "type": "heartbeat", "ts": "2026-04-06T..." }
```

---

## Privacy Safeguards

SHIELD-IoT is designed with privacy as a core principle:

- **Metadata only** — analyses packet headers, connection counts, and destination IPs. Never stores payload data.
- **Local processing** — all baseline models and anomaly detection run locally on your hardware.
- **Claude API** — only structured anomaly summaries (no raw traffic data) are sent for reasoning.
- **No cloud dependency** — falls back to rule-based reasoning if the Claude API is unavailable.
- **Open source** — every line of code is auditable under the MIT Licence.

---

## Production Deployment

See [`docs/deployment.md`](docs/deployment.md) for full ISP deployment guidance including:
- Raspberry Pi 4 deployment (recommended for home use)
- Docker Compose setup
- OpenWrt router integration
- Real passive traffic capture (replacing the simulator)

Image: 
image.png

---

## Societal Impact

SHIELD-IoT is built for the digital citizen who has never heard the term "intrusion detection" — families with smart home devices, senior citizens with connected health monitors, small business owners with IP cameras.

Every compromised baby monitor, every hacked router, every botnet-recruited smart TV represents a real person whose privacy was violated without them knowing. SHIELD-IoT makes **autonomous AI defence a basic digital right — not an enterprise luxury**.

---

## Licence

MIT Licence — see [LICENSE](LICENSE)

## Team

Built for iSAFE Hackathon 2026 — Track 2: Defend the Digital Citizen

> *The same AI capabilities attackers are using to compromise home networks in seconds are available to defenders. The only reason ordinary citizens remain unprotected is that no one has built an accessible, autonomous system for them. That is what we are here to do.*
