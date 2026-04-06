import type {
  Device,
  Alert,
  AttackScenario,
  NetworkStatus_Full,
  LiveConnection,
  ConnectionStats,
  BandwidthPoint,
  SecurityScore,
  IPInvestigationResult,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const WS_URL   = import.meta.env.VITE_WS_URL  || "ws://localhost:8000/ws";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  // Devices
  getDevices: () =>
    get<{ devices: Device[]; total: number }>("/devices/"),
  getDevice: (id: string) =>
    get<{ device: Device; baseline: unknown; is_isolated: boolean }>(`/devices/${id}`),
  restoreDevice: (id: string) =>
    post(`/devices/${id}/restore`, { reason: "Restored by user" }),
  getDevicePorts: (id: string) =>
    get<unknown>(`/devices/${id}/ports`),

  // Alerts
  getAlerts: (limit = 50) =>
    get<{ alerts: Alert[]; total: number; critical_count: number; high_count: number; medium_count: number }>(
      `/alerts/?limit=${limit}`
    ),
  getAlertSummary: () =>
    get<unknown>("/alerts/summary"),
  dismissAlert: (id: string) =>
    post(`/alerts/${id}/dismiss`),
  getReasoningLog: () =>
    get<{ reasoning_log: unknown[] }>("/alerts/reasoning/log"),

  // Network
  getNetworkStatus: () =>
    get<NetworkStatus_Full>("/network/status"),
  getThreatIntel: () =>
    get<unknown>("/network/threat-intelligence"),
  getActionLog: () =>
    get<{ actions: unknown[]; total: number }>("/network/action-log"),
  getBandwidth: () =>
    get<{ history: BandwidthPoint[]; current_sent_kbps: number; current_recv_kbps: number; peak_sent_kbps: number; peak_recv_kbps: number }>(
      "/network/bandwidth"
    ),
  getSecurityScore: () =>
    get<SecurityScore>("/network/security-score"),

  // Connections (real-data mode)
  getConnections: () =>
    get<{ connections: LiveConnection[]; stats: ConnectionStats }>("/connections/"),

  // IP Investigation
  investigateIP: (ip: string) =>
    get<IPInvestigationResult>(`/investigate/${encodeURIComponent(ip)}`),

  // Simulation
  getScenarios: () =>
    get<{ scenarios: AttackScenario[]; active_scenario: unknown }>("/network/simulation/scenarios"),
  startScenario: (id: string) =>
    post(`/network/simulation/start/${id}`),
  stopScenario: () =>
    post("/network/simulation/stop"),
};

export { WS_URL };
