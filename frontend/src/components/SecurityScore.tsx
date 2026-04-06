import { ShieldCheck, ShieldAlert, ShieldX, CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import type { SecurityScore as SecurityScoreType } from "../types";

interface Props {
  score: SecurityScoreType | null;
}

const GRADE_CONFIG = {
  A: { label: "Excellent", ringColor: "stroke-emerald-500", textColor: "text-emerald-700", bg: "bg-emerald-50", icon: ShieldCheck },
  B: { label: "Good",      ringColor: "stroke-sky-500",     textColor: "text-sky-700",     bg: "bg-sky-50",     icon: ShieldCheck },
  C: { label: "Fair",      ringColor: "stroke-yellow-500",  textColor: "text-yellow-700",  bg: "bg-yellow-50",  icon: ShieldAlert },
  D: { label: "Poor",      ringColor: "stroke-orange-500",  textColor: "text-orange-700",  bg: "bg-orange-50",  icon: ShieldAlert },
  F: { label: "Critical",  ringColor: "stroke-rose-500",    textColor: "text-rose-700",    bg: "bg-rose-50",    icon: ShieldX },
};

const STATUS_ICON = {
  pass: CheckCircle2,
  warn: AlertCircle,
  fail: XCircle,
};

const STATUS_COLOR = {
  pass: "text-emerald-600",
  warn: "text-amber-600",
  fail: "text-rose-600",
};

function CircleGauge({ score }: { score: number }) {
  const r = 40;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      {/* Track */}
      <circle cx="50" cy="50" r={r} fill="none" stroke="#e2e8f0" strokeWidth="8" />
      {/* Progress */}
      <circle
        cx="50" cy="50" r={r}
        fill="none"
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circ}`}
        transform="rotate(-90 50 50)"
        className={
          score >= 90 ? "stroke-emerald-500" :
          score >= 75 ? "stroke-sky-500" :
          score >= 60 ? "stroke-yellow-500" :
          score >= 45 ? "stroke-orange-500" :
          "stroke-rose-500"
        }
        style={{ transition: "stroke-dasharray 0.6s ease" }}
      />
      <text x="50" y="46" textAnchor="middle" className="text-slate-900" fontSize="18" fontWeight="700" fill="currentColor">
        {score}
      </text>
      <text x="50" y="60" textAnchor="middle" fontSize="10" fill="#94a3b8">/ 100</text>
    </svg>
  );
}

export function SecurityScore({ score: data }: Props) {
  if (!data) {
    return (
      <div className="card">
        <h2 className="section-title mb-4">Security Score</h2>
        <div className="flex items-center justify-center h-24 text-xs text-slate-400">
          Computing security posture…
        </div>
      </div>
    );
  }

  const grade   = data.grade as keyof typeof GRADE_CONFIG;
  const config  = GRADE_CONFIG[grade] ?? GRADE_CONFIG["F"];
  const GradeIcon = config.icon;

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <GradeIcon className={`w-4 h-4 ${config.textColor}`} />
        <h2 className="section-title">Security Score</h2>
        <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full ${config.bg} ${config.textColor}`}>
          Grade {data.grade} — {config.label}
        </span>
      </div>

      <div className="flex items-center gap-6 mb-4">
        <CircleGauge score={data.score} />
        <div className="flex-1 space-y-2">
          {data.factors.map((f, i) => {
            const StatusIcon = STATUS_ICON[f.status];
            return (
              <div key={i} className="flex items-center gap-2">
                <StatusIcon className={`w-3.5 h-3.5 shrink-0 ${STATUS_COLOR[f.status]}`} />
                <span className="text-xs text-slate-600 leading-tight flex-1">{f.name}</span>
                {f.deduction < 0 && (
                  <span className="text-xs font-mono text-rose-600 shrink-0">{f.deduction}</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {data.devices_scanned > 0 && (
        <p className="text-xs text-slate-400 border-t border-slate-100 pt-2">
          Port scan complete on {data.devices_scanned} device(s)
        </p>
      )}
    </div>
  );
}
