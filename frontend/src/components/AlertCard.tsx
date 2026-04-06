import { ChevronDown, ChevronUp, CheckCheck, Brain, Shield, Activity } from "lucide-react";
import { useState } from "react";
import { SeverityBadge } from "./SeverityBadge";
import { DeviceIcon } from "./DeviceIcon";
import type { Alert } from "../types";
import { formatDistanceToNow } from "date-fns";

interface Props {
  alert: Alert;
  onDismiss: (id: string) => void;
}

const actionLabels: Record<string, { label: string; color: string }> = {
  isolate: { label: "Device Isolated", color: "text-rose-700" },
  block_traffic: { label: "Traffic Blocked", color: "text-amber-700" },
  alert: { label: "Alert Generated", color: "text-yellow-700" },
  monitor: { label: "Monitoring", color: "text-sky-700" },
  quarantine: { label: "Quarantined", color: "text-violet-700" },
};

export function AlertCard({ alert, onDismiss }: Props) {
  const [expanded, setExpanded] = useState(false);
  const timeAgo = formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true });
  const action = actionLabels[alert.response_action] ?? { label: alert.response_action, color: "text-gray-400" };
  const dismissed = alert.status === "dismissed";

  return (
    <div className={`card border transition-all ${
      dismissed ? "opacity-50 border-slate-200" :
      alert.severity === "critical" ? "border-rose-200 bg-rose-50/70" :
      alert.severity === "high" ? "border-amber-200 bg-amber-50/70" :
      alert.severity === "medium" ? "border-yellow-200 bg-yellow-50/70" :
      "border-slate-200"
    }`}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${
          alert.severity === "critical" ? "bg-rose-100" :
          alert.severity === "high" ? "bg-amber-100" :
          "bg-yellow-100"
        }`}>
          <DeviceIcon type={alert.device_type} className="w-3.5 h-3.5 text-slate-700" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={alert.severity} />
            <span className="text-xs font-medium text-slate-700">{alert.attack_type}</span>
            <span className="text-xs text-slate-500 ml-auto">{timeAgo}</span>
          </div>
          <p className="text-xs text-slate-500 mb-1">{alert.device_name}</p>
          <p className="text-sm text-slate-700 leading-relaxed">{alert.plain_language_summary}</p>
        </div>
      </div>

      {/* Action taken */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-slate-500" />
          <span className={`text-xs font-medium ${action.color}`}>{action.label}</span>
          <span className="text-xs text-slate-500">— {alert.response_message?.split("(")[0].trim()}</span>
        </div>
        <div className="flex items-center gap-2">
          {!dismissed && (
            <button
              onClick={() => onDismiss(alert.id)}
              className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1 transition-colors"
            >
              <CheckCheck className="w-3 h-3" />
              Dismiss
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1 transition-colors"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            {expanded ? "Less" : "Details"}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 space-y-4 border-t border-slate-200 pt-4">
          {/* Confidence + scores */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-200">
              <p className="text-xs text-slate-500 mb-1">Confidence</p>
              <p className="text-lg font-bold text-slate-800">{Math.round(alert.confidence * 100)}%</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-200">
              <p className="text-xs text-slate-500 mb-1">ML Score</p>
              <p className="text-lg font-bold text-slate-800">{(alert.ml_score * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-200">
              <p className="text-xs text-slate-500 mb-1">Baseline</p>
              <p className="text-lg font-bold text-slate-800">{(alert.baseline_score * 100).toFixed(0)}%</p>
            </div>
          </div>

          {/* Agent reasoning steps */}
          {alert.reasoning_steps && alert.reasoning_steps.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Brain className="w-3.5 h-3.5 text-sky-700" />
                <span className="text-xs font-medium text-sky-700">Agent Reasoning Chain</span>
              </div>
              <div className="space-y-1.5">
                {alert.reasoning_steps.map((step, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-xs text-slate-500 shrink-0 mt-0.5">{i + 1}.</span>
                    <span className="text-xs text-slate-600">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rule matches */}
          {alert.rule_matches && alert.rule_matches.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Activity className="w-3.5 h-3.5 text-amber-700" />
                <span className="text-xs font-medium text-amber-700">Detection Signatures</span>
              </div>
              <div className="space-y-1.5">
                {alert.rule_matches.map((rule, i) => (
                  <div key={i} className="bg-slate-50 rounded-lg p-2.5 border border-slate-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-slate-700">{rule.name}</span>
                      <SeverityBadge severity={rule.severity} />
                    </div>
                    <p className="text-xs text-slate-600">{rule.description}</p>
                    <p className="text-xs text-slate-500 mt-1 font-mono">{rule.mitre_tactic}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical details */}
          {alert.technical_details && (
            <div>
              <p className="text-xs font-medium text-slate-600 mb-1.5">Technical Details</p>
              <p className="text-xs text-slate-600 bg-slate-50 rounded-lg p-2.5 border border-slate-200 font-mono leading-relaxed">{alert.technical_details}</p>
            </div>
          )}

          {/* User action */}
          {alert.recommended_user_action && (
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-3">
              <p className="text-xs font-medium text-sky-700 mb-1">Recommended Action</p>
              <p className="text-xs text-slate-700">{alert.recommended_user_action}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
