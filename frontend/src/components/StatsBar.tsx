import { Shield, AlertTriangle, Lock, Activity, Cpu } from "lucide-react";
import type { AgentStatus } from "../types";

interface Props {
  agentStatus: AgentStatus | null;
  criticalCount: number;
  highCount?: number;
}

export function StatsBar({ agentStatus, criticalCount }: Props) {
  const stats = [
    {
      icon: Cpu,
      label: "Devices Monitored",
      value: agentStatus?.total_devices ?? 0,
      color: "text-shield-400",
      bg: "bg-shield-500/10",
    },
    {
      icon: Activity,
      label: "Detection Cycles",
      value: agentStatus?.cycle_count?.toLocaleString() ?? "0",
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      icon: AlertTriangle,
      label: "Threats Detected",
      value: agentStatus?.threats_detected ?? 0,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
    },
    {
      icon: Lock,
      label: "Devices Isolated",
      value: agentStatus?.devices_isolated ?? 0,
      color: "text-red-400",
      bg: "bg-red-500/10",
    },
    {
      icon: Shield,
      label: "Critical Alerts",
      value: criticalCount,
      color: "text-red-400",
      bg: "bg-red-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.label} className="card border border-gray-800 flex items-center gap-3">
            <div className={`p-2 rounded-lg ${stat.bg} shrink-0`}>
              <Icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className="min-w-0">
              <p className="text-lg font-bold text-white leading-none">{stat.value}</p>
              <p className="text-xs text-gray-500 leading-tight mt-0.5">{stat.label}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
