"""
Agentic Reasoning Core — powered by Claude API
This is the AI brain of SHIELD-IoT. Given a structured anomaly alert,
Claude reasons about the threat, determines severity and response actions,
and generates a plain-language explanation for the user.
The agent maintains context across the conversation to reason over time.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are SHIELD, an autonomous AI cybersecurity agent protecting a home network.
Your role is to analyse suspicious network behaviour detected on IoT devices and:
1. Determine whether the anomaly is a genuine threat or a false positive
2. Assess the severity and likely attack type
3. Decide on the appropriate defensive response
4. Generate a plain-language explanation for a non-technical user

You have access to:
- Per-device behavioural baselines (what is normal for each device)
- Live threat intelligence (known malicious IPs, botnet C2 servers)
- Anomaly detection scores (ML model + rule-based signatures)
- Network topology (which devices are connected, their types)

Response format — always return valid JSON:
{
  "threat_confirmed": true/false,
  "confidence": 0.0-1.0,
  "severity": "low"|"medium"|"high"|"critical",
  "attack_type": "string describing the attack",
  "response_action": "monitor"|"alert"|"block_traffic"|"isolate"|"quarantine",
  "affected_devices": ["device_id_1", ...],
  "plain_language_summary": "2-3 sentence explanation for a non-technical user",
  "technical_details": "detailed technical analysis",
  "recommended_user_action": "what the user should do next",
  "false_positive_probability": 0.0-1.0,
  "reasoning_steps": ["step1", "step2", ...]
}

Be decisive. Home network users need clear, actionable guidance — not uncertainty.
When in doubt between isolating a device (disrupting service) and leaving it active (risk exposure),
err on the side of isolation if confidence > 0.7. User safety > device convenience.
"""


class ReasoningCore:
    """
    Claude-powered agentic reasoning for threat assessment.
    Maintains conversation history for contextual reasoning across incidents.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        is_real_key = api_key and not api_key.startswith("your_") and len(api_key) > 20
        if is_real_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
            logger.warning("No valid ANTHROPIC_API_KEY — reasoning core in rule-based simulation mode")

        self._conversation_history: list = []
        self._incident_log: list = []
        self.MAX_HISTORY = 20  # keep last 20 exchanges for context

    async def analyse_threat(
        self,
        detection_result: dict,
        device_info: dict,
        traffic_sample: dict,
        threat_intel_match: Optional[dict] = None,
    ) -> dict:
        """
        Core reasoning method. Takes detection data and returns a structured
        threat assessment with plain-language explanation.
        """
        context = self._build_context(
            detection_result, device_info, traffic_sample, threat_intel_match
        )

        if not self.client:
            return self._simulate_reasoning(detection_result, device_info)

        prompt = f"""
Analyse this network anomaly detected on a home IoT device:

{json.dumps(context, indent=2)}

Assess whether this is a genuine threat, determine the appropriate response,
and generate a plain-language explanation for the homeowner.
Remember: they are not technical — explain it like talking to a friend.
"""

        self._conversation_history.append({"role": "user", "content": prompt})
        if len(self._conversation_history) > self.MAX_HISTORY * 2:
            self._conversation_history = self._conversation_history[-self.MAX_HISTORY * 2:]

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=self._conversation_history,
            )
            assistant_message = response.content[0].text
            self._conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            reasoning = json.loads(assistant_message)
            reasoning["agent_model"] = "claude-opus-4-5"
            reasoning["reasoning_timestamp"] = datetime.now().isoformat()
            self._incident_log.append({
                "timestamp": reasoning["reasoning_timestamp"],
                "device_id": device_info.get("id"),
                "reasoning": reasoning,
            })
            return reasoning

        except json.JSONDecodeError as e:
            logger.error(f"Claude returned invalid JSON: {e}")
            return self._simulate_reasoning(detection_result, device_info)
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return self._simulate_reasoning(detection_result, device_info)

    def _build_context(
        self,
        detection_result: dict,
        device_info: dict,
        traffic_sample: dict,
        threat_intel_match: Optional[dict],
    ) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "device": {
                "id": device_info.get("id"),
                "name": device_info.get("name"),
                "type": device_info.get("type"),
                "manufacturer": device_info.get("manufacturer", "Unknown"),
                "ip_address": device_info.get("ip"),
                "mac_address": device_info.get("mac"),
                "last_seen": device_info.get("last_seen"),
            },
            "detection": {
                "ml_anomaly_score": detection_result.get("ml_score", 0),
                "baseline_anomaly_score": detection_result.get("baseline_score", 0),
                "rule_matches": detection_result.get("rule_matches", []),
                "attack_types_detected": detection_result.get("attack_types", []),
                "initial_severity": detection_result.get("severity"),
            },
            "traffic_snapshot": {
                "bytes_transferred_per_min": traffic_sample.get("bytes_transferred"),
                "connection_count": traffic_sample.get("connection_count"),
                "destination_host": traffic_sample.get("destination_host"),
                "destination_ip": traffic_sample.get("destination_ip"),
                "protocol": traffic_sample.get("protocol"),
                "outbound_ratio": traffic_sample.get("outbound_ratio"),
                "unique_destinations": traffic_sample.get("unique_dest_ips"),
                "unusual_ports": traffic_sample.get("unusual_ports", []),
            },
            "threat_intelligence": threat_intel_match or {"is_malicious": False},
            "network_context": {
                "total_devices_on_network": device_info.get("network_size", 8),
                "other_affected_devices": [],
            },
        }

    def _simulate_reasoning(self, detection_result: dict, device_info: dict) -> dict:
        """
        Fallback reasoning when Claude API is unavailable.
        Uses rule-based logic to produce a structured response.
        """
        severity = detection_result.get("severity", "low")
        attack_types = detection_result.get("attack_types", [])
        baseline_score = detection_result.get("baseline_score", 0)
        rule_matches = detection_result.get("rule_matches", [])

        device_name = device_info.get("name", "your device")
        device_type = device_info.get("type", "unknown")

        threat_confirmed = severity in ("high", "critical") or len(rule_matches) > 0
        confidence = min(0.95, baseline_score + 0.2 * len(rule_matches))

        response_map = {
            "critical": "isolate",
            "high": "block_traffic",
            "medium": "alert",
            "low": "monitor",
        }
        response_action = response_map.get(severity, "monitor")

        if attack_types:
            attack_name = attack_types[0].replace("_", " ").title()
        elif rule_matches:
            attack_name = rule_matches[0].get("name", "Suspicious Activity")
        else:
            attack_name = "Anomalous Behaviour"

        user_messages = {
            "critical": (
                f"We detected something serious on your {device_name}. "
                f"It appears to be involved in a {attack_name.lower()} attack. "
                f"We've automatically isolated this device from your network to protect your other devices and data."
            ),
            "high": (
                f"Your {device_name} is behaving unusually — it's sending data to unexpected places. "
                f"We've blocked the suspicious traffic. Keep an eye on this device."
            ),
            "medium": (
                f"Your {device_name} is doing something a bit unusual, but it might not be serious. "
                f"We're monitoring it closely and will take action if things get worse."
            ),
            "low": (
                f"We noticed a small deviation in your {device_name}'s behaviour, "
                f"but everything looks fine. No action needed."
            ),
        }

        reasoning_steps = [
            f"Checked {device_name} traffic against its learned behavioural baseline",
            f"Baseline anomaly score: {baseline_score:.2f} (threshold: 0.35)",
        ]
        if rule_matches:
            for m in rule_matches:
                reasoning_steps.append(f"Matched attack signature: {m['name']}")
        reasoning_steps.append(f"Final assessment: {severity.upper()} severity threat")
        reasoning_steps.append(f"Recommended response: {response_action}")

        return {
            "threat_confirmed": threat_confirmed,
            "confidence": round(confidence, 2),
            "severity": severity,
            "attack_type": attack_name,
            "response_action": response_action,
            "affected_devices": [device_info.get("id", "unknown")],
            "plain_language_summary": user_messages.get(severity, user_messages["low"]),
            "technical_details": (
                f"Baseline score: {baseline_score:.3f}. "
                f"Rules matched: {[m['name'] for m in rule_matches]}. "
                f"Attack patterns: {attack_types}."
            ),
            "recommended_user_action": (
                "Check your router admin panel and consider restarting the device after the threat is resolved."
                if threat_confirmed else "No action required."
            ),
            "false_positive_probability": round(max(0.0, 0.9 - confidence), 2),
            "reasoning_steps": reasoning_steps,
            "agent_model": "rule-based-fallback",
            "reasoning_timestamp": datetime.now().isoformat(),
        }

    def get_incident_log(self) -> list:
        return self._incident_log[-50:]

    def get_network_summary(self, devices: list, alerts: list) -> dict:
        """Generate a network-wide health summary using Claude."""
        if not self.client:
            return self._simulate_network_summary(devices, alerts)

        prompt = f"""
Provide a brief network health summary for a home with {len(devices)} connected devices.

Active alerts in the last hour: {len([a for a in alerts if a.get('severity') in ('high', 'critical')])} high/critical
Total alerts: {len(alerts)}

Device list: {[{'name': d.get('name'), 'type': d.get('type'), 'status': d.get('status')} for d in devices]}

Return JSON: {{
  "overall_status": "secure"|"warning"|"threat"|"critical",
  "threat_level": 0-10,
  "summary": "one sentence for a non-technical user",
  "top_recommendations": ["rec1", "rec2"]
}}
"""
        try:
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=512,
                system="You are a home network security advisor. Be concise and non-technical.",
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(response.content[0].text)
        except Exception:
            return self._simulate_network_summary(devices, alerts)

    def _simulate_network_summary(self, devices: list, alerts: list) -> dict:
        critical_alerts = [a for a in alerts if a.get("severity") in ("high", "critical")]
        if len(critical_alerts) > 0:
            status = "critical" if len(critical_alerts) > 2 else "threat"
            level = min(10, 5 + len(critical_alerts) * 2)
            summary = f"Your network has {len(critical_alerts)} active security threat(s) requiring attention."
        elif len(alerts) > 0:
            status = "warning"
            level = 3
            summary = f"Your network is mostly secure with {len(alerts)} minor alert(s) being monitored."
        else:
            status = "secure"
            level = 1
            summary = f"All {len(devices)} devices on your network are behaving normally."

        return {
            "overall_status": status,
            "threat_level": level,
            "summary": summary,
            "top_recommendations": [
                "Keep all device firmware updated",
                "Review any isolated devices before reconnecting",
            ],
        }


# Singleton
reasoning_core = ReasoningCore()
