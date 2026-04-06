import { Play, Square, Zap, AlertTriangle } from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import { SeverityBadge } from "./SeverityBadge";
import type { AttackScenario } from "../types";

interface Props {
  scenarios: AttackScenario[];
  activeScenario: unknown;
  onScenarioChange: () => void;
}

export function AttackSimPanel({ scenarios, activeScenario, onScenarioChange }: Props) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleStart = async (id: string) => {
    setLoading(id);
    try {
      await api.startScenario(id);
      onScenarioChange();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(null);
    }
  };

  const handleStop = async () => {
    setLoading("stop");
    try {
      await api.stopScenario();
      onScenarioChange();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(null);
    }
  };

  const active = activeScenario as { id?: string; name?: string } | null;

  return (
    <div className="card border border-gray-800">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-yellow-400" />
        <h2 className="text-sm font-semibold text-white">Attack Simulation</h2>
        <span className="text-xs text-gray-600 ml-auto">Demo mode</span>
      </div>

      {active && (
        <div className="mb-4 bg-red-900/20 border border-red-800/40 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-red-400">Active: {active.name}</span>
          </div>
          <button
            onClick={handleStop}
            disabled={loading === "stop"}
            className="flex items-center gap-1.5 text-xs text-red-400 bg-red-900/30 border border-red-800/40 rounded px-2 py-1 hover:bg-red-900/50 transition-colors disabled:opacity-50"
          >
            <Square className="w-3 h-3" />
            Stop
          </button>
        </div>
      )}

      <div className="space-y-2">
        {scenarios.map((scenario) => {
          const isActive = active?.id === scenario.id;
          const isLoading = loading === scenario.id;
          return (
            <div
              key={scenario.id}
              className={`border rounded-lg p-3 transition-all ${
                isActive ? "border-red-800/60 bg-red-950/20" : "border-gray-800 hover:border-gray-700"
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                    <span className="text-xs font-medium text-gray-200">{scenario.name}</span>
                    <SeverityBadge severity={scenario.severity} />
                  </div>
                  <p className="text-xs text-gray-500">Target: {scenario.device_name}</p>
                </div>
                <button
                  onClick={() => !isActive && !active ? handleStart(scenario.id) : undefined}
                  disabled={!!active || isLoading}
                  className={`shrink-0 flex items-center gap-1.5 text-xs rounded px-2.5 py-1.5 transition-colors ${
                    active
                      ? "text-gray-600 bg-gray-800 cursor-not-allowed"
                      : "text-emerald-400 bg-emerald-900/20 border border-emerald-800/40 hover:bg-emerald-900/40"
                  }`}
                >
                  <Play className="w-3 h-3" />
                  Run
                </button>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{scenario.description}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-4 border-t border-gray-800 pt-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-yellow-500 mt-0.5 shrink-0" />
          <p className="text-xs text-gray-600">
            These simulations inject realistic attack patterns into the traffic feed.
            SHIELD-IoT's agent will detect and respond autonomously — watch the alerts panel.
          </p>
        </div>
      </div>
    </div>
  );
}
