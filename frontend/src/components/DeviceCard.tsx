import { AlertTriangle, CheckCircle, Lock, RefreshCw, Clock } from "lucide-react";
import { DeviceIcon } from "./DeviceIcon";
import { SeverityBadge } from "./SeverityBadge";
import type { Device } from "../types";
import { formatDistanceToNow } from "date-fns";

interface Props {
  device: Device;
  onRestore: (id: string) => void;
  onClick: (device: Device) => void;
}

const statusStyles: Record<string, string> = {
  online: "border-slate-200 hover:border-slate-300",
  isolated: "border-rose-200 bg-rose-50 hover:border-rose-300",
  threat: "border-amber-200 bg-amber-50 hover:border-amber-300",
  warning: "border-yellow-200 bg-yellow-50 hover:border-yellow-300",
  offline: "border-slate-200 opacity-60",
};

const statusIcon: Record<string, React.ReactNode> = {
  online: <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />,
  isolated: <Lock className="w-3.5 h-3.5 text-rose-600" />,
  threat: <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-yellow-600" />,
  offline: <Clock className="w-3.5 h-3.5 text-slate-500" />,
};

export function DeviceCard({ device, onRestore, onClick }: Props) {
  const borderClass = statusStyles[device.status] ?? statusStyles.online;
  const lastSeen = device.last_seen
    ? formatDistanceToNow(new Date(device.last_seen), { addSuffix: true })
    : "unknown";

  return (
    <div
      className={`card border cursor-pointer transition-all ${borderClass}`}
      onClick={() => onClick(device)}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg ${device.status === "isolated" ? "bg-rose-100" : device.status === "threat" ? "bg-amber-100" : "bg-sky-100"}`}>
            <DeviceIcon type={device.type} className={`w-4 h-4 ${device.status === "isolated" ? "text-rose-600" : device.status === "threat" ? "text-amber-600" : "text-sky-700"}`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-800 truncate">{device.name}</p>
            <p className="text-xs text-slate-500">{device.manufacturer}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {statusIcon[device.status]}
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Status</span>
          <span className={`text-xs font-medium capitalize ${
            device.status === "isolated" ? "text-rose-700" :
            device.status === "threat" ? "text-amber-700" :
            device.status === "warning" ? "text-yellow-700" :
            "text-emerald-700"
          }`}>{device.status}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">IP</span>
          <span className="text-xs text-slate-600 font-mono">{device.ip}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">Last seen</span>
          <span className="text-xs text-slate-500">{lastSeen}</span>
        </div>
        {device.threat_level && device.threat_level !== "safe" && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">Threat</span>
            <SeverityBadge severity={device.threat_level} />
          </div>
        )}
      </div>

      {device.is_isolated && (
        <button
          className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg py-1.5 hover:bg-emerald-100 transition-colors"
          onClick={(e) => { e.stopPropagation(); onRestore(device.id); }}
        >
          <RefreshCw className="w-3 h-3" />
          Restore Device
        </button>
      )}
    </div>
  );
}
