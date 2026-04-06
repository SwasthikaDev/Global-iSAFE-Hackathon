import { Lock, ShieldX, Eye, Bell, RotateCcw } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Action {
  action: string;
  device_id: string;
  success: boolean;
  message: string;
  timestamp: string;
  simulated: boolean;
}

interface Props {
  actions: Action[];
}

const actionIcon: Record<string, React.ElementType> = {
  isolate: Lock,
  quarantine: ShieldX,
  block_traffic: ShieldX,
  alert: Bell,
  monitor: Eye,
  restore: RotateCcw,
};

const actionColor: Record<string, string> = {
  isolate: "text-red-400 bg-red-900/20",
  quarantine: "text-purple-400 bg-purple-900/20",
  block_traffic: "text-orange-400 bg-orange-900/20",
  alert: "text-yellow-400 bg-yellow-900/20",
  monitor: "text-blue-400 bg-blue-900/20",
  restore: "text-emerald-400 bg-emerald-900/20",
};

export function ActionLog({ actions }: Props) {
  return (
    <div className="card border border-gray-800">
      <h3 className="text-sm font-semibold text-white mb-4">Autonomous Action Log</h3>
      {actions.length === 0 ? (
        <p className="text-xs text-gray-600 text-center py-6">No actions taken yet</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {[...actions].reverse().map((action, i) => {
            const Icon = actionIcon[action.action] ?? Eye;
            const colorClass = actionColor[action.action] ?? "text-gray-400 bg-gray-800/50";
            const timeAgo = formatDistanceToNow(new Date(action.timestamp), { addSuffix: true });
            return (
              <div key={i} className="flex items-start gap-2.5">
                <div className={`mt-0.5 p-1.5 rounded-md shrink-0 ${colorClass}`}>
                  <Icon className="w-3 h-3" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-gray-300 capitalize">{action.action.replace("_", " ")}</span>
                    <span className="text-xs text-gray-600 shrink-0">{timeAgo}</span>
                  </div>
                  <p className="text-xs text-gray-500 truncate">{action.message}</p>
                  {action.simulated && (
                    <span className="text-xs text-gray-700">(simulated)</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
