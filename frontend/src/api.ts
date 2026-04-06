const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

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
  getDevices: () => get<{ devices: import("./types").Device[]; total: number }>("/devices/"),
  getDevice: (id: string) => get<{ device: import("./types").Device; baseline: unknown; is_isolated: boolean }>(`/devices/${id}`),
  restoreDevice: (id: string) => post(`/devices/${id}/restore`, { reason: "Restored by user" }),

  // Alerts
  getAlerts: (limit = 50) => get<{ alerts: import("./types").Alert[]; total: number; critical_count: number; high_count: number; medium_count: number }>(`/alerts/?limit=${limit}`),
  getAlertSummary: () => get<unknown>("/alerts/summary"),
  dismissAlert: (id: string) => post(`/alerts/${id}/dismiss`),
  getReasoningLog: () => get<{ reasoning_log: unknown[] }>("/alerts/reasoning/log"),

  // Network
  getNetworkStatus: () => get<import("./types").NetworkStatus_Full>("/network/status"),
  getThreatIntel: () => get<unknown>("/network/threat-intelligence"),
  getActionLog: () => get<{ actions: unknown[]; total: number }>("/network/action-log"),

  // Simulation
  getScenarios: () => get<{ scenarios: import("./types").AttackScenario[]; active_scenario: unknown }>("/network/simulation/scenarios"),
  startScenario: (id: string) => post(`/network/simulation/start/${id}`),
  stopScenario: () => post("/network/simulation/stop"),
};

export { WS_URL };
