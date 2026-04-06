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
      color: "text-sky-700",
      bg: "bg-sky-100",
    },
    {
      icon: Activity,
      label: "Detection Cycles",
      value: agentStatus?.cycle_count?.toLocaleString() ?? "0",
      color: "text-blue-700",
      bg: "bg-blue-100",
    },
    {
      icon: AlertTriangle,
      label: "Threats Detected",
      value: agentStatus?.threats_detected ?? 0,
      color: "text-amber-700",
      bg: "bg-amber-100",
    },
    {
      icon: Lock,
      label: "Devices Isolated",
      value: agentStatus?.devices_isolated ?? 0,
      color: "text-rose-700",
      bg: "bg-rose-100",
    },
    {
      icon: Shield,
      label: "Critical Alerts",
      value: criticalCount,
      color: "text-rose-700",
      bg: "bg-rose-100",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.label} className="card flex items-center gap-3">
            <div className={`p-2 rounded-lg ${stat.bg} shrink-0`}>
              <Icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className="min-w-0">
              <p className="text-lg font-bold text-slate-800 leading-none">{stat.value}</p>
              <p className="text-xs text-slate-500 leading-tight mt-0.5">{stat.label}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
