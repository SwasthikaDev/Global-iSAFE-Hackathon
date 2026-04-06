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
  isolate: "text-rose-700 bg-rose-100",
  quarantine: "text-violet-700 bg-violet-100",
  block_traffic: "text-amber-700 bg-amber-100",
  alert: "text-yellow-700 bg-yellow-100",
  monitor: "text-sky-700 bg-sky-100",
  restore: "text-emerald-700 bg-emerald-100",
};

export function ActionLog({ actions }: Props) {
  return (
    <div className="card">
      <h3 className="section-title mb-4">Autonomous Action Log</h3>
      {actions.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-6">No actions taken yet</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {[...actions].reverse().map((action, i) => {
            const Icon = actionIcon[action.action] ?? Eye;
            const colorClass = actionColor[action.action] ?? "text-slate-600 bg-slate-100";
            const timeAgo = formatDistanceToNow(new Date(action.timestamp), { addSuffix: true });
            return (
              <div key={i} className="flex items-start gap-2.5">
                <div className={`mt-0.5 p-1.5 rounded-md shrink-0 ${colorClass}`}>
                  <Icon className="w-3 h-3" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-slate-700 capitalize">{action.action.replace("_", " ")}</span>
                    <span className="text-xs text-slate-500 shrink-0">{timeAgo}</span>
                  </div>
                  <p className="text-xs text-slate-500 truncate">{action.message}</p>
                  {action.simulated && (
                    <span className="text-xs text-slate-400">(simulated)</span>
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
