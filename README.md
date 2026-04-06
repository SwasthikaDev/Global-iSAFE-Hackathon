# SHIELD-IoT 🛡️
### Agentic AI for Autonomous Home Network Defence

> **iSAFE Hackathon 2026 — Track 2: Defend the Digital Citizen**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.35-blue.svg)](https://flutter.dev)

---

## The Problem

The average household has 10–15 smart IoT devices — cameras, baby monitors, smart speakers, thermostats — each running lightweight firmware with minimal security. AI-driven IoT attacks surged 54% in 2026. Autonomous malware now compromises a device in under 60 seconds.

**The citizen has no defence.** Intrusion detection systems require deep expertise and cost thousands. Nothing equivalent exists for ordinary people.

## The Solution

SHIELD-IoT is an **agentic AI system** that autonomously monitors, detects, and neutralises cyber threats targeting smart devices on a home network — with **zero technical knowledge required** from the user.

---

## Two Frontends, One Powerful Backend

SHIELD-IoT ships with **two complete frontends** that both connect to the same Python backend, so you can monitor your network from anywhere:

### 🖥️ Web Dashboard — React + TypeScript
> For desktop/browser access — full feature set on a large screen.

- Real-time threat monitoring with live WebSocket push updates
- Security posture score (0–100, grade A–F) with factor breakdown
- Live TCP connection table with country flags, ISP and process names
- Per-device port scan results and anomaly history
- Bandwidth chart (upload / download in KB/s)
- IP Investigator — enter any IP and get geolocation, threat intel, open ports and active connections in one click
- Attack simulation panel (demo mode)

**Run it:**
```bash
cd frontend && npm install && npm run dev
# Opens at http://localhost:5173
```

---

### 📱 Mobile App — Flutter (Android & iOS)
> For on-the-go monitoring — same data, optimised for your phone.

- All six screens mirroring the web dashboard: Dashboard, Devices, Alerts, Traffic, IP Investigator, Settings
- Security score arc gauge with live threat badge on the nav bar
- Bandwidth line chart powered by fl_chart
- Tap any device for a full detail bottom sheet including port scan summary
- IP Investigator with quick-pick buttons for common LAN addresses
- Configurable server URL — point the app at any machine running the backend on your local Wi-Fi
- WebSocket real-time updates + 5-second auto-refresh
- Supports Android (API 21+) and iOS (13+)

**Run it:**
```bash
cd shield_iot_mobile && flutter pub get && flutter run
# Set backend URL in Settings → e.g. http://192.168.1.x:8000
```

---

### How They Connect

```
┌──────────────────────────┐        ┌────────────────────────────┐
│   Web Dashboard          │        │   Mobile App               │
│   React + TypeScript     │        │   Flutter (Android / iOS)  │
│   http://localhost:5173  │        │   Any device on the LAN    │
└───────────┬──────────────┘        └────────────┬───────────────┘
            │  REST + WebSocket                   │  REST + WebSocket
            └──────────────┬──────────────────────┘
                           ▼
              ┌────────────────────────┐
              │   SHIELD-IoT Backend   │
              │   FastAPI + Python     │
              │   Real-time AI agent   │
              └────────────────────────┘
```

Both frontends consume the **same REST API and WebSocket stream** — no duplication of logic, all intelligence lives in the backend.

### How It Works — Four Continuous Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHIELD-IoT Agent Loop                        │
│                                                                  │
│  1. OBSERVE ──► 2. REASON ──► 3. ACT ──► 4. EXPLAIN            │
│                                                                  │
│  Passive traffic    LLM-based      Isolate device    Plain     │
│  monitoring +       threat          Block traffic     language  │
│  per-device         assessment      Log forensics     alert     │
│  baseline                                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Screenshots

![SHIELD-IoT Dashboard](img1.png)

![Security Score & Devices](img2.png)

![Live Connections](img3.png)

![IP Investigator](img4.png)

![Alerts Panel](img5.png)

![Mobile App — Dashboard](img6.png)

![Mobile App — Investigate](img7.png)

---

## Quick Start

### Prerequisites
| Requirement | For |
|---|---|
| Python 3.11+ | Backend |
| Node.js 18+ | Web frontend |
| Flutter 3.35+ | Mobile app |
| LLM API key | Optional — rule-based fallback built in |

### 1 — Start the Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # add your API keys
python main.py                # starts at http://localhost:8000
```

### 2a — Open the Web Dashboard

```bash
cd frontend
npm install
npm run dev                   # opens http://localhost:5173
```

### 2b — Run the Mobile App

```bash
cd shield_iot_mobile
flutter pub get
flutter run                   # connects to http://10.0.2.2:8000 on emulator
                              # change URL in Settings for a real device
```

> You can run **both frontends at the same time** — they share the same backend.

### Running a Demo

1. Start the backend — real network monitoring begins immediately
2. Open the web dashboard **or** the mobile app (or both)
3. Check the **Security Score** card to see your current network posture
4. Use the **IP Investigator** to scan any device on your network
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
│   │   ├── reasoning_core.py      # LLM agentic reasoning
│   │   ├── response_executor.py   # Autonomous response (isolate/block)
│   │   ├── geo_lookup.py          # IP geolocation enrichment
│   │   ├── port_scanner.py        # Async LAN port scanner
│   │   └── threat_intel.py        # Live threat intelligence feeds
│   ├── api/routes/
│   │   ├── devices.py             # Device management endpoints
│   │   ├── alerts.py              # Alert management endpoints
│   │   ├── network.py             # Network status, score, bandwidth
│   │   ├── connections.py         # Live TCP connection endpoint
│   │   └── investigate.py         # IP investigation endpoint
│   └── simulation/
│       ├── network_sim.py         # Realistic IoT traffic simulation
│       └── attack_sim.py          # Attack scenario engine
├── frontend/
│   └── src/
│       ├── App.tsx                # Main dashboard
│       ├── components/            # UI components
│       └── hooks/useWebSocket.ts  # Real-time WebSocket connection
└── shield_iot_mobile/             # Flutter mobile app
    └── lib/
        ├── main.dart
        ├── screens/               # Dashboard, Devices, Alerts, Connections, Investigate
        ├── services/              # API client + Provider state
        └── widgets/               # Reusable UI components
```

### Technical Stack

| Component | Technology |
|-----------|-----------|
| Agentic Reasoning | LLM API (rule-based fallback included) |
| Anomaly Detection | Isolation Forest (scikit-learn) |
| Behavioural Baseline | Exponential Moving Average per device |
| Backend API | FastAPI + WebSockets |
| Traffic Monitoring | psutil — OS-level TCP connection capture |
| Device Discovery | ARP cache scan |
| Geolocation | ip-api.com batch API |
| Threat Intelligence | AbuseIPDB + built-in IOC list |
| Port Scanning | Async TCP probe |
| Frontend Dashboard | React 18 + TypeScript + Tailwind CSS |
| Mobile App | Flutter 3.35 (Android + iOS) |
| Charts | Recharts (web), fl_chart (mobile) |

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

Full interactive docs are available at `/docs` once the backend is running.

### Endpoint Groups

- **`/api/devices/`** — device list, detail, port scan, baseline, isolation
- **`/api/alerts/`** — alert list, detail, reasoning log, dismiss
- **`/api/network/`** — status, security score, bandwidth history, threat intel, action log
- **`/api/connections/`** — live TCP connection snapshot with geo enrichment
- **`/api/investigate/{ip}`** — full parallel intelligence lookup for any IP

### WebSocket — Real-Time Events

Connect to `ws://<host>/ws` to receive push events:

```json
{ "type": "alert",         "data": { ... } }
{ "type": "device_update", "data": { ... } }
{ "type": "status_update", "data": { ... } }
{ "type": "heartbeat",     "ts":   "..." }
```

---

## Privacy Safeguards

SHIELD-IoT is designed with privacy as a core principle:

- **Metadata only** — analyses packet headers, connection counts, and destination IPs. Never stores payload data.
- **Local processing** — all baseline models and anomaly detection run locally on your hardware.
- **LLM API** — only structured anomaly summaries (no raw traffic data) are sent for reasoning.
- **No cloud dependency** — falls back to rule-based reasoning if the LLM API is unavailable.
- **Open source** — every line of code is auditable under the MIT Licence.

---

## Production Deployment

See [`docs/deployment.md`](docs/deployment.md) for full deployment guidance including:
- Raspberry Pi 4 deployment (recommended for home use)
- Docker Compose setup
- OpenWrt router integration
- Real passive traffic capture

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
