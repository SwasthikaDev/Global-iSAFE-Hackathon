import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "./api";
import { useWebSocket } from "./hooks/useWebSocket";
import { NetworkStatusHeader } from "./components/NetworkStatusHeader";
import { StatsBar } from "./components/StatsBar";
import { DeviceCard } from "./components/DeviceCard";
import { AlertCard } from "./components/AlertCard";
import { AttackSimPanel } from "./components/AttackSimPanel";
import { ThreatChart } from "./components/ThreatChart";
import { ActionLog } from "./components/ActionLog";
import type {
  Device,
  Alert,
  AgentStatus,
  NetworkStatus,
  AttackScenario,
  WSMessage,
} from "./types";

export default function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [threatLevel, setThreatLevel] = useState(0);
  const [networkSummary, setNetworkSummary] = useState("");
  const [scenarios, setScenarios] = useState<AttackScenario[]>([]);
  const [activeScenario, setActiveScenario] = useState<unknown>(null);
  const [actionLog, setActionLog] = useState<unknown[]>([]);
  const [criticalCount, setCriticalCount] = useState(0);
  const [highCount, setHighCount] = useState(0);
  const [activeTab, setActiveTab] = useState<"alerts" | "devices">("alerts");

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [devRes, alertRes, netRes, actRes] = await Promise.all([
        api.getDevices(),
        api.getAlerts(100),
        api.getNetworkStatus(),
        api.getActionLog(),
      ]);
      setDevices(devRes.devices);
      setAlerts(alertRes.alerts);
      setCriticalCount(alertRes.critical_count);
      setHighCount(alertRes.high_count);
      setAgentStatus(netRes.agent);
      setNetworkStatus(netRes.network_summary.overall_status);
      setThreatLevel(netRes.network_summary.threat_level);
      setNetworkSummary(netRes.network_summary.summary);
      setActionLog(actRes.actions);
    } catch (e) {
      console.error("Data load error:", e);
    }
  }, []);

  const loadScenarios = useCallback(async () => {
    try {
      const res = await api.getScenarios();
      setScenarios(res.scenarios);
      setActiveScenario(res.active_scenario);
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Handle WebSocket messages for real-time updates
  const handleWsMessage = useCallback((msg: WSMessage) => {
    if (msg.type === "incident") {
      const incident = msg.data as Alert;
      setAlerts((prev) => {
        const exists = prev.some((a) => a.id === incident.id);
        if (exists) return prev;
        return [incident, ...prev].slice(0, 200);
      });
      // Update device status
      setDevices((prev) =>
        prev.map((d) =>
          d.id === incident.device_id
            ? { ...d, status: incident.response_action === "isolate" ? "isolated" : "threat", threat_level: incident.severity, is_isolated: incident.response_action === "isolate" }
            : d
        )
      );
      // Bump counters
      if (incident.severity === "critical") setCriticalCount((n) => n + 1);
      if (incident.severity === "high") setHighCount((n) => n + 1);
      setActionLog((prev) => [{
        action: incident.response_action,
        device_id: incident.device_id,
        success: incident.response_success,
        message: incident.response_message,
        timestamp: incident.timestamp,
        simulated: true,
      }, ...prev].slice(0, 100));
    } else if (msg.type === "status_update") {
      const data = msg.data as AgentStatus;
      setAgentStatus(data);
    }
  }, []);

  const { connected } = useWebSocket(handleWsMessage);

  useEffect(() => {
    loadData();
    loadScenarios();
    // Poll every 5 seconds as fallback
    pollingRef.current = setInterval(loadData, 5000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [loadData, loadScenarios]);

  const handleDismissAlert = async (id: string) => {
    try {
      await api.dismissAlert(id);
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, status: "dismissed" } : a));
    } catch (e) {
      console.error(e);
    }
  };

  const handleRestoreDevice = async (id: string) => {
    try {
      await api.restoreDevice(id);
      setDevices((prev) =>
        prev.map((d) => d.id === id ? { ...d, status: "online", threat_level: "safe", is_isolated: false } : d)
      );
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeviceClick = (_device: Device) => {
    // Could open a device detail modal
  };

  const activeAlerts = alerts.filter((a) => a.status === "active");

  return (
    <div className="min-h-screen bg-slate-50">
      <NetworkStatusHeader
        networkStatus={networkStatus}
        threatLevel={threatLevel}
        summary={networkSummary}
        agentStatus={agentStatus}
        wsConnected={connected}
      />

      <main className="max-w-7xl mx-auto px-4 py-5 space-y-5">
        {/* Stats */}
        <StatsBar agentStatus={agentStatus} criticalCount={criticalCount} highCount={highCount} />

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Left column: Devices + Chart + Action Log */}
          <div className="lg:col-span-1 space-y-4">
            {/* Threat Activity Chart */}
            <ThreatChart alerts={alerts} />

            {/* Devices */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Network Devices</h2>
                <span className="muted">{devices.length} devices</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2.5">
                {devices.map((device) => (
                  <DeviceCard
                    key={device.id}
                    device={device}
                    onRestore={handleRestoreDevice}
                    onClick={handleDeviceClick}
                  />
                ))}
              </div>
            </div>

            {/* Action Log */}
            <ActionLog actions={actionLog as Parameters<typeof ActionLog>[0]["actions"]} />
          </div>

          {/* Right column: Alerts + Simulation */}
          <div className="lg:col-span-2 space-y-4">
            {/* Attack Simulation Panel */}
            <AttackSimPanel
              scenarios={scenarios}
              activeScenario={activeScenario}
              onScenarioChange={() => { loadScenarios(); loadData(); }}
            />

            {/* Tabs */}
            <div>
              <div className="flex gap-1 mb-3 bg-slate-100 border border-slate-200 rounded-lg p-1 w-fit">
                <button
                  onClick={() => setActiveTab("alerts")}
                  className={`text-xs px-3 py-1.5 rounded-md transition-colors font-medium ${
                    activeTab === "alerts"
                      ? "bg-white text-slate-800 shadow-sm border border-slate-200"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  Alerts {activeAlerts.length > 0 && (
                    <span className="ml-1.5 bg-rose-600 text-white text-xs rounded-full px-1.5 py-0.5">
                      {activeAlerts.length}
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveTab("devices")}
                  className={`text-xs px-3 py-1.5 rounded-md transition-colors font-medium ${
                    activeTab === "devices"
                      ? "bg-white text-slate-800 shadow-sm border border-slate-200"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  All Activity
                </button>
              </div>

              {activeTab === "alerts" && (
                <div className="space-y-2">
                  {activeAlerts.length === 0 ? (
                    <div className="card text-center py-12">
                      <div className="text-4xl mb-3">🛡️</div>
                      <p className="text-sm font-medium text-slate-800 mb-1">All Clear</p>
                      <p className="text-xs text-slate-500">
                        No active threats detected. Run an attack simulation to see SHIELD-IoT in action.
                      </p>
                    </div>
                  ) : (
                    activeAlerts.map((alert) => (
                      <AlertCard key={alert.id} alert={alert} onDismiss={handleDismissAlert} />
                    ))
                  )}
                </div>
              )}

              {activeTab === "devices" && (
                <div className="space-y-2">
                  {alerts.slice(0, 50).map((alert) => (
                    <AlertCard key={alert.id} alert={alert} onDismiss={handleDismissAlert} />
                  ))}
                  {alerts.length === 0 && (
                    <div className="card text-center py-12">
                      <p className="text-xs text-slate-500">No activity recorded yet</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-slate-200 pt-4 pb-2 text-center">
          <p className="text-xs text-slate-500">
            SHIELD-IoT — Agentic AI for Autonomous Home Network Defence · Track 2: Defend the Digital Citizen · iSAFE Hackathon 2026
          </p>
          <p className="text-xs text-slate-400 mt-1">
            MIT Licence · Powered by Claude API · Open source on GitHub
          </p>
        </footer>
      </main>
    </div>
  );
}
