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
  online: "border-gray-800 hover:border-gray-700",
  isolated: "border-red-800/60 bg-red-950/20 hover:border-red-700",
  threat: "border-orange-800/60 bg-orange-950/20 hover:border-orange-700",
  warning: "border-yellow-800/60 bg-yellow-950/20 hover:border-yellow-700",
  offline: "border-gray-800 opacity-60",
};

const statusIcon: Record<string, React.ReactNode> = {
  online: <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />,
  isolated: <Lock className="w-3.5 h-3.5 text-red-400" />,
  threat: <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />,
  warning: <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" />,
  offline: <Clock className="w-3.5 h-3.5 text-gray-500" />,
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
          <div className={`p-2 rounded-lg ${device.status === "isolated" ? "bg-red-900/40" : device.status === "threat" ? "bg-orange-900/40" : "bg-gray-800"}`}>
            <DeviceIcon type={device.type} className={`w-4 h-4 ${device.status === "isolated" ? "text-red-400" : device.status === "threat" ? "text-orange-400" : "text-shield-400"}`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{device.name}</p>
            <p className="text-xs text-gray-500">{device.manufacturer}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {statusIcon[device.status]}
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Status</span>
          <span className={`text-xs font-medium capitalize ${
            device.status === "isolated" ? "text-red-400" :
            device.status === "threat" ? "text-orange-400" :
            device.status === "warning" ? "text-yellow-400" :
            "text-emerald-400"
          }`}>{device.status}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">IP</span>
          <span className="text-xs text-gray-400 font-mono">{device.ip}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-600">Last seen</span>
          <span className="text-xs text-gray-500">{lastSeen}</span>
        </div>
        {device.threat_level && device.threat_level !== "safe" && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">Threat</span>
            <SeverityBadge severity={device.threat_level} />
          </div>
        )}
      </div>

      {device.is_isolated && (
        <button
          className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs text-emerald-400 bg-emerald-900/20 border border-emerald-800/40 rounded-lg py-1.5 hover:bg-emerald-900/40 transition-colors"
          onClick={(e) => { e.stopPropagation(); onRestore(device.id); }}
        >
          <RefreshCw className="w-3 h-3" />
          Restore Device
        </button>
      )}
    </div>
  );
}
