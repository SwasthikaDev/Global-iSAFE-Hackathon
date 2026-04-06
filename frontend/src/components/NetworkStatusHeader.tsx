import { Shield, ShieldAlert, ShieldCheck, ShieldX, Wifi, WifiOff } from "lucide-react";
import type { NetworkStatus, AgentStatus } from "../types";

interface Props {
  networkStatus: NetworkStatus | null;
  threatLevel: number;
  summary: string;
  agentStatus: AgentStatus | null;
  wsConnected: boolean;
}

const statusConfig = {
  secure: {
    icon: ShieldCheck,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/30",
    label: "SECURE",
    pulse: "bg-emerald-500",
  },
  warning: {
    icon: Shield,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10 border-yellow-500/30",
    label: "WARNING",
    pulse: "bg-yellow-500",
  },
  threat: {
    icon: ShieldAlert,
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/30",
    label: "THREAT DETECTED",
    pulse: "bg-orange-500",
  },
  critical: {
    icon: ShieldX,
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/30",
    label: "CRITICAL",
    pulse: "bg-red-500",
  },
};

export function NetworkStatusHeader({ networkStatus, threatLevel, summary, agentStatus, wsConnected }: Props) {
  const config = statusConfig[networkStatus ?? "secure"];
  const Icon = config.icon;

  return (
    <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative">
            <Shield className="w-8 h-8 text-shield-400" />
            <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-shield-400 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white leading-none">SHIELD-IoT</h1>
            <p className="text-xs text-gray-500 leading-none mt-0.5">Autonomous Home Network Defence</p>
          </div>
        </div>

        {/* Network Status */}
        <div className={`flex items-center gap-2.5 border rounded-lg px-3 py-2 ${config.bg}`}>
          <div className={`relative flex h-2.5 w-2.5`}>
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.pulse} opacity-75`} />
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${config.pulse}`} />
          </div>
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className={`text-sm font-semibold ${config.color}`}>{config.label}</span>
          {threatLevel > 0 && (
            <span className={`text-xs ${config.color} opacity-75`}>Level {threatLevel}/10</span>
          )}
        </div>

        {/* Summary */}
        {summary && (
          <p className="text-sm text-gray-400 hidden lg:block flex-1 text-center truncate max-w-md">
            {summary}
          </p>
        )}

        {/* Agent + WS Status */}
        <div className="flex items-center gap-3 shrink-0">
          {agentStatus && (
            <div className="text-right hidden sm:block">
              <p className="text-xs text-gray-500">Cycles: <span className="text-gray-300">{agentStatus.cycle_count.toLocaleString()}</span></p>
              <p className="text-xs text-gray-500">Threats: <span className="text-red-400">{agentStatus.threats_detected}</span></p>
            </div>
          )}
          <div className={`flex items-center gap-1.5 text-xs ${wsConnected ? "text-emerald-400" : "text-gray-600"}`}>
            {wsConnected ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{wsConnected ? "Live" : "Reconnecting..."}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
