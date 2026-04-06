# SHIELD-IoT — Technical Architecture

## System Overview

SHIELD-IoT is a multi-layer autonomous defence system operating in a continuous four-phase loop. Each component is independently replaceable and the system gracefully degrades if external services are unavailable.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SHIELD-IoT Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   HOME NETWORK                    SHIELD-IoT ENGINE                         │
│   ┌──────────────┐                ┌─────────────────────────────────────┐   │
│   │ Smart TV     │──traffic──────►│ 1. OBSERVE                          │   │
│   │ IP Camera    │  metadata      │    PassiveMonitor (pcap/simulated)  │   │
│   │ Baby Monitor │                │    ↓                                │   │
│   │ Thermostat   │                │ 2. REASON (two layers)              │   │
│   │ Smart Plug   │                │    BaselineManager (EMA per device) │   │
│   │ Smart Speaker│                │    AnomalyDetector (Isolation Forest│   │
│   │ Router       │                │    + rule signatures)               │   │
│   └──────────────┘                │    ↓ (if anomaly detected)          │   │
│          ▲                        │    ReasoningCore (Claude API)        │   │
│          │                        │    ↓                                │   │
│   Router firewall rules           │ 3. ACT                              │   │
│          │                        │    ResponseExecutor                 │   │
│   ┌──────┴───────┐                │    (isolate / block / alert)        │   │
│   │  ASUS/OpenWrt│◄───REST API────│    ↓                                │   │
│   │  Router      │                │ 4. EXPLAIN                          │   │
│   └──────────────┘                │    Plain-language incident report   │   │
│                                   └────────────┬────────────────────────┘   │
│                                                │                             │
│                                   ┌────────────▼────────────────────────┐   │
│                                   │    FastAPI + WebSocket Server        │   │
│                                   └────────────┬────────────────────────┘   │
│                                                │ Real-time events           │
│                                   ┌────────────▼────────────────────────┐   │
│                                   │    React Dashboard                   │   │
│                                   │    (alerts, devices, action log)    │   │
│                                   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detection Pipeline

### Layer 1 — Behavioural Baseline (baseline.py)

Each device receives an individual statistical profile using **Exponential Moving Average (EMA)** learning:

- **Bandwidth profile**: Max bytes/minute, rolling average, standard deviation
- **Connection profile**: Frequency, unique destinations, protocol distribution
- **Temporal profile**: Active hours, connection regularity
- **Destination profile**: Known-good server whitelist, auto-populated from observed traffic

Anomaly scores are computed per-feature and combined into a weighted composite score (0.0–1.0):

| Feature | Weight | Rationale |
|---------|--------|-----------|
| Bandwidth deviation | 30% | Exfiltration and DDoS show clear bandwidth anomalies |
| Connection frequency | 25% | C2 beaconing creates unusual connection patterns |
| Destination novelty | 25% | Attacks communicate with new, unknown destinations |
| Time-of-day | 10% | Overnight activity from dormant devices is suspicious |
| Packet size | 10% | Tunnelling and exfil often use atypical packet sizes |

### Layer 2 — ML Anomaly Detection (anomaly_detector.py)

**Isolation Forest** (scikit-learn) provides unsupervised outlier detection:
- Trained on observed normal traffic (min 30 samples)
- 10 engineered features per sample
- Contamination parameter: 5% (assumes ~5% of traffic may be anomalous)
- Normalised anomaly score maps Isolation Forest output to [0, 1]

**Rule-based signatures** catch known attack patterns immediately:

| Rule | Detection Condition | MITRE Tactic |
|------|--------------------|----|
| Port Scan | >15 unique destination ports/min | TA0043 Reconnaissance |
| Botnet C2 Beacon | >95% connection regularity | TA0011 C&C |
| Data Exfiltration | Bytes > 3x baseline, outbound ratio > 90% | TA0010 Exfiltration |
| Brute Force | >10 failed connections to service ports | TA0006 Credential Access |
| DNS Tunnelling | >100 DNS queries, avg payload >150 bytes | TA0011 C&C |
| Lateral Movement | >20 connections to >5 internal IPs | TA0008 Lateral Movement |
| Firmware Attack | Inbound mgmt connection from external IP | TA0001 Initial Access |

### Layer 3 — Agentic Reasoning (reasoning_core.py)

Claude API receives a structured context object containing:
- Device profile and current traffic snapshot
- Baseline anomaly scores with feature breakdown
- Rule-based signature matches
- Threat intelligence lookup results
- Network topology context

Claude reasons through:
1. Whether the anomaly is a genuine threat or false positive
2. Severity classification (low/medium/high/critical)
3. Most likely attack type and MITRE technique
4. Appropriate response action
5. Plain-language explanation for the homeowner

**Fallback**: If the Claude API is unavailable, a rule-based reasoning engine produces structurally identical output.

## Response Actions

| Action | Trigger | Implementation |
|--------|---------|----------------|
| `monitor` | Score < 0.35 | Enhanced logging, no disruption |
| `alert` | Score 0.35–0.55 | User notification, continued monitoring |
| `block_traffic` | High severity, specific IP | Router firewall rule via REST API |
| `isolate` | Critical severity | Full device network isolation (VLAN or firewall) |
| `quarantine` | Critical + forensics | Isolation + PCAP capture enabled |

## Threat Intelligence

SHIELD-IoT maintains a curated IOC (Indicator of Compromise) database:
- Known botnet C2 servers (Mirai, Mozi, Gafgyt, BotenaGo families)
- Known scanner IPs (mass IoT vulnerability scanners)
- DDoS infrastructure
- Optional: Live enrichment from AbuseIPDB (requires API key)

## Data Flow

```
Traffic Sample → BaselineManager.update()
              → BaselineManager.score()      → anomaly_score dict
              → ThreatIntel.check_ip()       → threat_intel_match dict
              → AnomalyDetector.detect()     → detection_result dict
              → ReasoningCore.analyse()      → reasoning dict (Claude)
              → ResponseExecutor.execute()   → action_result dict
              → Incident created             → WebSocket broadcast
              → Alert stored                 → Dashboard updated
```

## WebSocket Protocol

Real-time events are broadcast to all connected dashboard clients:

```typescript
// Incident alert (new threat detected)
{ type: "incident", data: Alert }

// Agent status update (every cycle)
{ type: "status_update", data: AgentStatus }

// Keep-alive
{ type: "heartbeat", ts: string }
```

## Simulation Architecture

The simulation layer replaces real pcap capture for the hackathon demo:

```
NetworkSimulator.generate_traffic()
  └── For each device:
        if attack injected: _generate_attack_traffic()
        else: _generate_normal_traffic()
  └── Returns list[TrafficSample]

AttackSimulator.start_scenario(id)
  └── NetworkSimulator.inject_attack(device_id, config)
  └── Advances through phases each cycle
```

Traffic patterns are based on published IoT traffic datasets:
- UNSW-NB15 dataset (normal/abnormal network traffic)
- N-BaIoT dataset (IoT device traffic + Mirai/BASHLITE attacks)
- IEEE IoT-23 dataset (labelled IoT network traffic)
