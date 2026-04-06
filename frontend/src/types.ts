export type Severity = "critical" | "high" | "medium" | "low";
export type DeviceStatus = "online" | "isolated" | "threat" | "warning" | "offline";
export type NetworkStatus = "secure" | "warning" | "threat" | "critical";

export interface PortScanInfo {
  risk_level: "none" | "low" | "medium" | "high" | "critical" | "unknown";
  open_port_count: number | null;
  dangerous_ports: { port: number; service: string; risk: string }[];
  scan_time: string | null;
}

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
  port_scan?: PortScanInfo;
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
  threat_intel?: { is_malicious: boolean; details?: unknown };
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
  type: "connected" | "incident" | "status_update" | "heartbeat" | "pong" | "device_added";
  data?: unknown;
  ts?: string;
}

// ── New types for v2 features ─────────────────────────────────────────────────

export interface LiveConnection {
  local_port: number;
  remote_ip: string;
  remote_port: number;
  hostname: string;
  protocol: string;
  process_name: string;
  process_pid: number | null;
  is_outbound: boolean;
  is_private: boolean;
  country: string;
  country_name: string;
  city: string;
  isp: string;
  flag: string;
  is_high_risk_country: boolean;
  is_suspicious_isp: boolean;
  is_malicious_ip: boolean;
  is_suspicious: boolean;
}

export interface ConnectionStats {
  total: number;
  external: number;
  internal: number;
  suspicious: number;
  top_processes: { name: string; count: number }[];
  top_countries: { code: string; count: number }[];
  unique_remote_ips: number;
}

export interface BandwidthPoint {
  ts: string;
  sent_kbps: number;
  recv_kbps: number;
}

export interface SecurityScoreFactor {
  name: string;
  deduction: number;
  status: "pass" | "warn" | "fail";
}

export interface SecurityScore {
  score: number;
  grade: string;
  color: string;
  factors: SecurityScoreFactor[];
  devices_scanned: number;
  timestamp: string;
}
