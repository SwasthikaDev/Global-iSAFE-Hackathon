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
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-amber-600" />
        <h2 className="section-title">Attack Simulation</h2>
        <span className="muted ml-auto">Demo mode</span>
      </div>

      {active && (
        <div className="mb-4 bg-rose-50 border border-rose-200 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-rose-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-rose-700">Active: {active.name}</span>
          </div>
          <button
            onClick={handleStop}
            disabled={loading === "stop"}
            className="flex items-center gap-1.5 text-xs text-rose-700 bg-white border border-rose-200 rounded px-2 py-1 hover:bg-rose-100 transition-colors disabled:opacity-50"
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
                isActive ? "border-rose-200 bg-rose-50/70" : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                    <span className="text-xs font-medium text-slate-700">{scenario.name}</span>
                    <SeverityBadge severity={scenario.severity} />
                  </div>
                  <p className="text-xs text-slate-500">Target: {scenario.device_name}</p>
                </div>
                <button
                  onClick={() => !isActive && !active ? handleStart(scenario.id) : undefined}
                  disabled={!!active || isLoading}
                  className={`shrink-0 flex items-center gap-1.5 text-xs rounded px-2.5 py-1.5 transition-colors ${
                    active
                      ? "text-slate-400 bg-slate-100 cursor-not-allowed"
                      : "text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100"
                  }`}
                >
                  <Play className="w-3 h-3" />
                  Run
                </button>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">{scenario.description}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-4 border-t border-slate-200 pt-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
          <p className="text-xs text-slate-500">
            These simulations inject realistic attack patterns into the traffic feed.
            SHIELD-IoT's agent will detect and respond autonomously — watch the alerts panel.
          </p>
        </div>
      </div>
    </div>
  );
}
