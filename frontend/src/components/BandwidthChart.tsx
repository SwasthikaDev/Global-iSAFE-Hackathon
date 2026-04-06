import { ArrowUp, ArrowDown } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { BandwidthPoint } from "../types";

interface Props {
  history: BandwidthPoint[];
  currentSent: number;
  currentRecv: number;
}

function fmt(kbps: number): string {
  if (kbps >= 1024) return `${(kbps / 1024).toFixed(1)} MB/s`;
  return `${kbps.toFixed(0)} KB/s`;
}

function tickTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm px-3 py-2 text-xs">
      <p className="text-slate-400 mb-1">{label}</p>
      <p className="text-sky-600">↑ Upload: {fmt(payload[0]?.value ?? 0)}</p>
      <p className="text-emerald-600">↓ Download: {fmt(payload[1]?.value ?? 0)}</p>
    </div>
  );
};

export function BandwidthChart({ history, currentSent, currentRecv }: Props) {
  const data = history.map(h => ({
    time: tickTime(h.ts),
    sent: h.sent_kbps,
    recv: h.recv_kbps,
  }));

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="section-title">Live Bandwidth</h2>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-sky-600">
            <ArrowUp className="w-3 h-3" />
            <span className="font-mono font-medium">{fmt(currentSent)}</span>
          </span>
          <span className="flex items-center gap-1 text-emerald-600">
            <ArrowDown className="w-3 h-3" />
            <span className="font-mono font-medium">{fmt(currentRecv)}</span>
          </span>
        </div>
      </div>

      {data.length < 2 ? (
        <div className="h-32 flex items-center justify-center text-xs text-slate-400">
          Collecting bandwidth data…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
            <defs>
              <linearGradient id="bwSent" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="bwRecv" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 9, fill: "#94a3b8" }}
              interval="preserveStartEnd"
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 9, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => v >= 1024 ? `${(v/1024).toFixed(0)}M` : `${v}K`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="sent"
              name="Upload"
              stroke="#0ea5e9"
              strokeWidth={1.5}
              fill="url(#bwSent)"
              dot={false}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="recv"
              name="Download"
              stroke="#10b981"
              strokeWidth={1.5}
              fill="url(#bwRecv)"
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      <div className="flex items-center gap-4 mt-2 justify-end">
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="w-3 h-0.5 bg-sky-400 rounded inline-block" />
          Upload
        </span>
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="w-3 h-0.5 bg-emerald-400 rounded inline-block" />
          Download
        </span>
      </div>
    </div>
  );
}
