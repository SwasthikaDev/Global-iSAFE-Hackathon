# SHIELD-IoT — Privacy Safeguards

## Privacy-by-Design Principles

SHIELD-IoT is built from the ground up with privacy as a core architectural constraint, not an afterthought.

## What We Analyse vs. What We Never Touch

| Data Category | SHIELD-IoT Status | Details |
|---------------|------------------|---------|
| Packet payload (content) | **Never collected** | HTTP bodies, file contents, voice data — never inspected or stored |
| Connection metadata | **Analysed, not stored** | Source/dest IP, port, protocol, byte count — processed and discarded |
| DNS queries | **Query count only** | Number of DNS lookups per minute — not the actual domain names queried |
| Destination IPs | **Checked against IOC list** | Only flagged if matching a known malicious IP — otherwise discarded |
| Device MAC addresses | **Used for identification** | Stored locally only, never transmitted externally |
| Behavioural baseline | **Stored locally** | Statistical profiles (averages, thresholds) — no raw traffic data |

## Data Flow with Privacy Annotations

```
Raw Traffic Packet
    │
    ▼ [PRIVACY GATE: only metadata extracted, payload discarded]
    │
Traffic Metadata: {src_ip, dst_ip, dst_port, protocol, byte_count, timestamp}
    │
    ▼ [LOCAL PROCESSING: baseline comparison, anomaly scoring]
    │
Anomaly Summary: {device_id, score, feature_deltas, matched_rules}
    │
    ▼ [PRIVACY GATE: no raw IPs or hostnames in Claude prompt unless malicious]
    │
Claude API Input: {anomaly_score, device_type, traffic_statistics, rule_matches}
    │
    ▼ [Claude reasons about patterns, not content]
    │
Reasoning Output: {severity, attack_type, plain_language_explanation}
```

## What Is Sent to the Claude API

Only structured, statistical summaries:

```json
{
  "device": { "type": "ip_camera", "manufacturer": "Ring" },
  "detection": {
    "ml_anomaly_score": 0.87,
    "baseline_anomaly_score": 0.92,
    "rule_matches": ["Data Exfiltration"],
    "attack_types_detected": ["exfiltration"]
  },
  "traffic_snapshot": {
    "bytes_transferred_per_min": 15000000,
    "connection_count": 3,
    "outbound_ratio": 0.98
  },
  "threat_intelligence": { "is_malicious": true, "category": "exfil_endpoint" }
}
```

**What is NOT sent to Claude:**
- Packet contents or payloads
- Full list of websites visited
- Voice or video stream data
- Personal device identifiers beyond type/manufacturer
- Raw IP addresses of non-malicious destinations

## Local-First Architecture

All core processing runs on the user's local hardware:
- Behavioural baseline models: local SQLite / in-memory
- Isolation Forest model: saved locally as `.joblib`
- Threat intelligence IOC list: bundled in the application
- Incident logs: stored locally, never sent to external servers

The Claude API is the only external service call, and it receives only the anomaly summary (not raw traffic).

## GDPR Compliance Notes

| GDPR Requirement | SHIELD-IoT Implementation |
|-----------------|--------------------------|
| Article 5 — Data minimisation | Only metadata processed; payload never collected |
| Article 25 — Privacy by Design | Privacy controls built into core architecture |
| Article 32 — Security | Local processing; TLS for all API communications |
| Article 17 — Right to erasure | Clear data with `DELETE /api/data` endpoint (production) |
| Article 13 — Transparency | This document + full open-source code |

## Responsible Disclosure

SHIELD-IoT is designed to protect home users. If you discover a privacy vulnerability, please report it responsibly via GitHub Issues.
