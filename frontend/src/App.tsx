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
import { ConnectionsPanel } from "./components/ConnectionsPanel";
import { BandwidthChart } from "./components/BandwidthChart";
import { SecurityScore } from "./components/SecurityScore";
import type {
  Device,
  Alert,
  AgentStatus,
  NetworkStatus,
  AttackScenario,
  WSMessage,
  LiveConnection,
  ConnectionStats,
  BandwidthPoint,
  SecurityScore as SecurityScoreType,
} from "./types";

export default function App() {
  const [devices,          setDevices]          = useState<Device[]>([]);
  const [alerts,           setAlerts]           = useState<Alert[]>([]);
  const [agentStatus,      setAgentStatus]      = useState<AgentStatus | null>(null);
  const [networkStatus,    setNetworkStatus]    = useState<NetworkStatus | null>(null);
  const [threatLevel,      setThreatLevel]      = useState(0);
  const [networkSummary,   setNetworkSummary]   = useState("");
  const [scenarios,        setScenarios]        = useState<AttackScenario[]>([]);
  const [activeScenario,   setActiveScenario]   = useState<unknown>(null);
  const [actionLog,        setActionLog]        = useState<unknown[]>([]);
  const [criticalCount,    setCriticalCount]    = useState(0);
  const [highCount,        setHighCount]        = useState(0);
  const [dataMode,         setDataMode]         = useState<"simulation" | "real">("simulation");
  const [activeTab,        setActiveTab]        = useState<"alerts" | "activity" | "connections">("alerts");

  // New v2 state
  const [connections,      setConnections]      = useState<LiveConnection[]>([]);
  const [connStats,        setConnStats]        = useState<ConnectionStats | null>(null);
  const [bandwidthHistory, setBandwidthHistory] = useState<BandwidthPoint[]>([]);
  const [bwSent,           setBwSent]           = useState(0);
  const [bwRecv,           setBwRecv]           = useState(0);
  const [securityScore,    setSecurityScore]    = useState<SecurityScoreType | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const connPollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Core data load ──────────────────────────────────────────────────────────
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
      setDataMode(netRes.mode === "real" ? "real" : "simulation");
      setActionLog(actRes.actions);
    } catch (e) {
      console.error("Data load error:", e);
    }
  }, []);

  // ── Real-data only: connections + bandwidth + security score ────────────────
  const loadRealData = useCallback(async () => {
    try {
      const [connRes, bwRes, scoreRes] = await Promise.all([
        api.getConnections(),
        api.getBandwidth(),
        api.getSecurityScore(),
      ]);
      setConnections(connRes.connections ?? []);
      setConnStats(connRes.stats ?? null);
      setBandwidthHistory(bwRes.history ?? []);
      setBwSent(bwRes.current_sent_kbps ?? 0);
      setBwRecv(bwRes.current_recv_kbps ?? 0);
      setSecurityScore(scoreRes);
    } catch (e) {
      // Silently ignore — connections endpoint returns empty in sim mode
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

  // ── WebSocket messages ──────────────────────────────────────────────────────
  const handleWsMessage = useCallback((msg: WSMessage) => {
    if (msg.type === "incident") {
      const incident = msg.data as Alert;
      setAlerts(prev => {
        if (prev.some(a => a.id === incident.id)) return prev;
        return [incident, ...prev].slice(0, 200);
      });
      setDevices(prev =>
        prev.map(d =>
          d.id === incident.device_id
            ? {
                ...d,
                status: incident.response_action === "isolate" ? "isolated" : "threat",
                threat_level: incident.severity,
                is_isolated: incident.response_action === "isolate",
              }
            : d
        )
      );
      if (incident.severity === "critical") setCriticalCount(n => n + 1);
      if (incident.severity === "high")     setHighCount(n => n + 1);
      setActionLog(prev => [{
        action: incident.response_action,
        device_id: incident.device_id,
        success: incident.response_success,
        message: incident.response_message,
        timestamp: incident.timestamp,
        simulated: dataMode === "simulation",
      }, ...prev].slice(0, 100));
    } else if (msg.type === "status_update") {
      setAgentStatus(msg.data as AgentStatus);
    } else if (msg.type === "device_added") {
      loadData();
    }
  }, [dataMode, loadData]);

  const { connected } = useWebSocket(handleWsMessage);

  // ── Polling ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    loadData();
    loadScenarios();
    loadRealData();
    pollingRef.current     = setInterval(loadData,     5000);
    connPollingRef.current = setInterval(loadRealData, 3000);
    return () => {
      if (pollingRef.current)     clearInterval(pollingRef.current);
      if (connPollingRef.current) clearInterval(connPollingRef.current);
    };
  }, [loadData, loadScenarios, loadRealData]);

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleDismissAlert = async (id: string) => {
    try {
      await api.dismissAlert(id);
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: "dismissed" } : a));
    } catch (e) { console.error(e); }
  };

  const handleRestoreDevice = async (id: string) => {
    try {
      await api.restoreDevice(id);
      setDevices(prev =>
        prev.map(d => d.id === id ? { ...d, status: "online", threat_level: "safe", is_isolated: false } : d)
      );
    } catch (e) { console.error(e); }
  };

  const activeAlerts = alerts.filter(a => a.status === "active");

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
        <StatsBar
          agentStatus={agentStatus}
          criticalCount={criticalCount}
          highCount={highCount}
        />

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* ── Left column ──────────────────────────────────────────────── */}
          <div className="lg:col-span-1 space-y-4">
            {/* Bandwidth chart (real mode) / Threat chart (sim mode) */}
            {dataMode === "real" ? (
              <BandwidthChart
                history={bandwidthHistory}
                currentSent={bwSent}
                currentRecv={bwRecv}
              />
            ) : (
              <ThreatChart alerts={alerts} />
            )}

            {/* Security score */}
            <SecurityScore score={securityScore} />

            {/* Devices */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Network Devices</h2>
                <span className="muted">{devices.length} device{devices.length !== 1 ? "s" : ""}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2.5">
                {devices.map(device => (
                  <DeviceCard
                    key={device.id}
                    device={device}
                    onRestore={handleRestoreDevice}
                    onClick={() => {}}
                  />
                ))}
              </div>
            </div>

            {/* Action log */}
            <ActionLog actions={actionLog as Parameters<typeof ActionLog>[0]["actions"]} />
          </div>

          {/* ── Right column ─────────────────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-4">
            {/* Simulation / Live Monitor panel */}
            <AttackSimPanel
              scenarios={scenarios}
              activeScenario={activeScenario}
              onScenarioChange={() => { loadScenarios(); loadData(); }}
              dataMode={dataMode}
            />

            {/* Tabs */}
            <div>
              <div className="flex gap-1 mb-3 bg-slate-100 border border-slate-200 rounded-lg p-1 w-fit">
                {(["alerts", "activity", ...(dataMode === "real" ? ["connections"] : [])] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab as typeof activeTab)}
                    className={`text-xs px-3 py-1.5 rounded-md transition-colors font-medium capitalize ${
                      activeTab === tab
                        ? "bg-white text-slate-800 shadow-sm border border-slate-200"
                        : "text-slate-500 hover:text-slate-700"
                    }`}
                  >
                    {tab === "alerts" ? (
                      <>
                        Alerts
                        {activeAlerts.length > 0 && (
                          <span className="ml-1.5 bg-rose-600 text-white text-xs rounded-full px-1.5 py-0.5">
                            {activeAlerts.length}
                          </span>
                        )}
                      </>
                    ) : tab === "connections" ? (
                      <>
                        Live Connections
                        {(connStats?.suspicious ?? 0) > 0 && (
                          <span className="ml-1.5 bg-amber-500 text-white text-xs rounded-full px-1.5 py-0.5">
                            {connStats!.suspicious}
                          </span>
                        )}
                      </>
                    ) : "Activity"}
                  </button>
                ))}
              </div>

              {/* Alerts tab */}
              {activeTab === "alerts" && (
                <div className="space-y-2">
                  {activeAlerts.length === 0 ? (
                    <div className="card text-center py-12">
                      <div className="text-4xl mb-3">🛡️</div>
                      <p className="text-sm font-medium text-slate-800 mb-1">All Clear</p>
                      <p className="text-xs text-slate-500">
                        {dataMode === "real"
                          ? "No threats detected. SHIELD-IoT is actively monitoring your live network traffic."
                          : "No active threats. Run an attack simulation to see SHIELD-IoT in action."}
                      </p>
                    </div>
                  ) : (
                    activeAlerts.map(alert => (
                      <AlertCard key={alert.id} alert={alert} onDismiss={handleDismissAlert} />
                    ))
                  )}
                </div>
              )}

              {/* Activity tab */}
              {activeTab === "activity" && (
                <div className="space-y-2">
                  {alerts.length === 0 ? (
                    <div className="card text-center py-12">
                      <p className="text-xs text-slate-500">No activity recorded yet</p>
                    </div>
                  ) : (
                    alerts.slice(0, 50).map(alert => (
                      <AlertCard key={alert.id} alert={alert} onDismiss={handleDismissAlert} />
                    ))
                  )}
                </div>
              )}

              {/* Live connections tab (real mode only) */}
              {activeTab === "connections" && dataMode === "real" && (
                <ConnectionsPanel connections={connections} stats={connStats} />
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="border-t border-slate-200 pt-4 pb-2 text-center">
          <p className="text-xs text-slate-500">
            SHIELD-IoT · Agentic AI for Autonomous Home Network Defence · Track 2: Defend the Digital Citizen · iSAFE Hackathon 2026
          </p>
          <p className="text-xs text-slate-400 mt-1">
            MIT Licence · Powered by Claude API · Open source on GitHub
          </p>
        </footer>
      </main>
    </div>
  );
}
