export type Severity = "critical" | "high" | "medium" | "low";
export type DeviceStatus = "online" | "isolated" | "threat" | "warning" | "offline";
export type NetworkStatus = "secure" | "warning" | "threat" | "critical";

export interface Device {
  id: string;
  name: string;
  type: string;
  manufacturer: string;
  ip: string;
  mac: string;
  model: string;
  firmware: string;
  status: DeviceStatus;
  threat_level: string;
  last_seen: string;
  is_isolated: boolean;
}

export interface Alert {
  id: string;
  timestamp: string;
  device_id: string;
  device_name: string;
  device_type: string;
  severity: Severity;
  attack_type: string;
  threat_confirmed: boolean;
  confidence: number;
  plain_language_summary: string;
  technical_details: string;
  recommended_user_action: string;
  response_action: string;
  response_success: boolean;
  response_message: string;
  reasoning_steps: string[];
  ml_score: number;
  baseline_score: number;
  rule_matches: RuleMatch[];
  false_positive_probability: number;
  status: "active" | "dismissed";
}

export interface RuleMatch {
  name: string;
  description: string;
  severity: Severity;
  attack_type: string;
  mitre_tactic: string;
}

export interface AgentStatus {
  running: boolean;
  cycle_count: number;
  last_cycle: string | null;
  threats_detected: number;
  devices_isolated: number;
  total_devices: number;
  total_alerts: number;
  isolated_devices: string[];
  blocked_ips: string[];
  start_time: string | null;
}

export interface NetworkSummary {
  overall_status: NetworkStatus;
  threat_level: number;
  summary: string;
  top_recommendations: string[];
}

export interface NetworkStatus_Full {
  agent: AgentStatus;
  network_summary: NetworkSummary;
  device_count: number;
  alert_count: number;
  isolated_devices: string[];
  blocked_ips: string[];
  mode?: "simulation" | "real";
}

export interface AttackScenario {
  id: string;
  name: string;
  description: string;
  device_name: string;
  severity: Severity;
}

export interface WSMessage {
  type: "connected" | "incident" | "status_update" | "heartbeat" | "pong";
  data?: unknown;
  ts?: string;
}
