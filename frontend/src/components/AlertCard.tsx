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
  isolate: { label: "Device Isolated", color: "text-red-400" },
  block_traffic: { label: "Traffic Blocked", color: "text-orange-400" },
  alert: { label: "Alert Generated", color: "text-yellow-400" },
  monitor: { label: "Monitoring", color: "text-blue-400" },
  quarantine: { label: "Quarantined", color: "text-purple-400" },
};

export function AlertCard({ alert, onDismiss }: Props) {
  const [expanded, setExpanded] = useState(false);
  const timeAgo = formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true });
  const action = actionLabels[alert.response_action] ?? { label: alert.response_action, color: "text-gray-400" };
  const dismissed = alert.status === "dismissed";

  return (
    <div className={`card border transition-all ${
      dismissed ? "opacity-50 border-gray-800" :
      alert.severity === "critical" ? "border-red-800/60 bg-red-950/10" :
      alert.severity === "high" ? "border-orange-800/60 bg-orange-950/10" :
      alert.severity === "medium" ? "border-yellow-800/60 bg-yellow-950/10" :
      "border-gray-800"
    }`}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${
          alert.severity === "critical" ? "bg-red-900/40" :
          alert.severity === "high" ? "bg-orange-900/40" :
          "bg-yellow-900/40"
        }`}>
          <DeviceIcon type={alert.device_type} className="w-3.5 h-3.5 text-gray-300" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={alert.severity} />
            <span className="text-xs font-medium text-gray-300">{alert.attack_type}</span>
            <span className="text-xs text-gray-600 ml-auto">{timeAgo}</span>
          </div>
          <p className="text-xs text-gray-500 mb-1">{alert.device_name}</p>
          <p className="text-sm text-gray-300 leading-relaxed">{alert.plain_language_summary}</p>
        </div>
      </div>

      {/* Action taken */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-gray-600" />
          <span className={`text-xs font-medium ${action.color}`}>{action.label}</span>
          <span className="text-xs text-gray-600">— {alert.response_message?.split("(")[0].trim()}</span>
        </div>
        <div className="flex items-center gap-2">
          {!dismissed && (
            <button
              onClick={() => onDismiss(alert.id)}
              className="text-xs text-gray-600 hover:text-gray-400 flex items-center gap-1 transition-colors"
            >
              <CheckCheck className="w-3 h-3" />
              Dismiss
            </button>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-600 hover:text-gray-400 flex items-center gap-1 transition-colors"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            {expanded ? "Less" : "Details"}
          </button>
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 space-y-4 border-t border-gray-800 pt-4">
          {/* Confidence + scores */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-800/50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-500 mb-1">Confidence</p>
              <p className="text-lg font-bold text-white">{Math.round(alert.confidence * 100)}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-500 mb-1">ML Score</p>
              <p className="text-lg font-bold text-white">{(alert.ml_score * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-500 mb-1">Baseline</p>
              <p className="text-lg font-bold text-white">{(alert.baseline_score * 100).toFixed(0)}%</p>
            </div>
          </div>

          {/* Agent reasoning steps */}
          {alert.reasoning_steps && alert.reasoning_steps.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Brain className="w-3.5 h-3.5 text-shield-400" />
                <span className="text-xs font-medium text-shield-400">Agent Reasoning Chain</span>
              </div>
              <div className="space-y-1.5">
                {alert.reasoning_steps.map((step, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-xs text-gray-600 shrink-0 mt-0.5">{i + 1}.</span>
                    <span className="text-xs text-gray-400">{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rule matches */}
          {alert.rule_matches && alert.rule_matches.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Activity className="w-3.5 h-3.5 text-orange-400" />
                <span className="text-xs font-medium text-orange-400">Detection Signatures</span>
              </div>
              <div className="space-y-1.5">
                {alert.rule_matches.map((rule, i) => (
                  <div key={i} className="bg-gray-800/50 rounded-lg p-2.5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-300">{rule.name}</span>
                      <SeverityBadge severity={rule.severity} />
                    </div>
                    <p className="text-xs text-gray-500">{rule.description}</p>
                    <p className="text-xs text-gray-600 mt-1 font-mono">{rule.mitre_tactic}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical details */}
          {alert.technical_details && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1.5">Technical Details</p>
              <p className="text-xs text-gray-500 bg-gray-800/50 rounded-lg p-2.5 font-mono leading-relaxed">{alert.technical_details}</p>
            </div>
          )}

          {/* User action */}
          {alert.recommended_user_action && (
            <div className="bg-shield-900/20 border border-shield-800/30 rounded-lg p-3">
              <p className="text-xs font-medium text-shield-400 mb-1">Recommended Action</p>
              <p className="text-xs text-gray-300">{alert.recommended_user_action}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
