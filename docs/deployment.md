# SHIELD-IoT — Deployment Guide

## Development (Simulation Mode)

The default mode uses a built-in IoT network simulator — no hardware or network access required.

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Production Deployment on Raspberry Pi 4

Recommended hardware: Raspberry Pi 4 (4GB RAM), connected to home router via Ethernet.

### 1. Install Dependencies

```bash
sudo apt update && sudo apt install -y python3.11 python3-pip nodejs npm git
pip3 install -r backend/requirements.txt
```

### 2. Configure Real Traffic Capture

In production, replace the simulator with passive pcap capture using `scapy` or `tcpdump`:

```bash
sudo apt install -y tcpdump
pip3 install scapy
```

Edit `backend/.env`:
```
SIMULATION_MODE=false
NETWORK_INTERFACE=eth0   # Your network interface
```

### 3. Router API Integration

SHIELD-IoT uses the router's REST API for device isolation. Supported routers:

| Router Firmware | API Endpoint | Notes |
|----------------|-------------|-------|
| OpenWrt (LuCI) | `http://router/cgi-bin/luci/api/` | Recommended |
| DD-WRT | `http://router/apply.cgi` | Partial support |
| ASUS Merlin | `http://router/appGet.cgi` | Requires custom script |
| Generic | iptables via SSH | Fallback method |

Configure in `.env`:
```
ROUTER_IP=192.168.1.1
ROUTER_USERNAME=admin
ROUTER_PASSWORD=your_password
```

### 4. Systemd Service

```ini
# /etc/systemd/system/shield-iot.service
[Unit]
Description=SHIELD-IoT Security Agent
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/shield-iot/backend
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/pi/shield-iot/backend

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable shield-iot
sudo systemctl start shield-iot
```

---

## Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SIMULATION_MODE=true
    volumes:
      - ./backend/.env:/app/.env
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## ISP-Scale Deployment

For ISP deployment protecting entire subscriber networks:

### Architecture Changes Required

1. **Replace per-home simulator** with a distributed traffic collection layer using NetFlow/IPFIX from CPE routers
2. **Scale the inference layer** — deploy multiple instances with a load balancer
3. **Centralise threat intelligence** — shared IOC database across all subscribers
4. **Multi-tenant Claude API** — use separate API keys or rate-limit per subscriber
5. **Replace in-memory alert store** with PostgreSQL/TimescaleDB for time-series data

### Privacy at Scale

ISP deployment must enforce:
- **No payload inspection** — only connection metadata (5-tuple) is analysed
- **On-premise processing** — subscriber traffic metadata never leaves the ISP's infrastructure
- **Subscriber consent** — opt-in service with clear privacy disclosure
- **Data retention limits** — traffic metadata purged after 7 days (adjustable)
- **Regulatory compliance** — GDPR Article 25 (Privacy by Design), PECR

### Reference Network Architecture

```
Subscriber CPE Router
    │ (NetFlow/IPFIX metadata)
    ▼
ISP Collection Layer (Kafka)
    │
    ▼
SHIELD-IoT Processing Cluster
    ├── Baseline workers (one per subscriber)
    ├── Anomaly detection workers
    └── Claude API reasoning (batched)
    │
    ▼
Subscriber Portal (React Dashboard)
    + SMS/Email alerts
```

---

## Security Hardening

For production deployments:

1. **HTTPS only** — terminate TLS at nginx proxy
2. **API authentication** — add JWT bearer tokens to all API routes
3. **WebSocket auth** — validate token on WebSocket handshake
4. **Rate limiting** — add `slowapi` middleware to FastAPI
5. **Secrets management** — use environment variables or HashiCorp Vault, never hardcode
6. **Model file integrity** — verify SHA256 of saved model files on startup
