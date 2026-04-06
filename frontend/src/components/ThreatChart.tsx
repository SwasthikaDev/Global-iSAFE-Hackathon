import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { Alert } from "../types";
import { useMemo } from "react";
import { format, subMinutes, startOfMinute } from "date-fns";

interface Props {
  alerts: Alert[];
}

export function ThreatChart({ alerts }: Props) {
  const data = useMemo(() => {
    const now = new Date();
    const buckets: Record<string, { time: string; critical: number; high: number; medium: number }> = {};

    // Create 10-minute window with 1-minute buckets
    for (let i = 9; i >= 0; i--) {
      const t = startOfMinute(subMinutes(now, i));
      const key = format(t, "HH:mm");
      buckets[key] = { time: key, critical: 0, high: 0, medium: 0 };
    }

    for (const alert of alerts) {
      const t = startOfMinute(new Date(alert.timestamp));
      const key = format(t, "HH:mm");
      if (key in buckets) {
        const sev = alert.severity as keyof typeof buckets[typeof key];
        if (sev === "critical" || sev === "high" || sev === "medium") {
          buckets[key][sev]++;
        }
      }
    }

    return Object.values(buckets);
  }, [alerts]);

  return (
    <div className="card border border-gray-800">
      <h3 className="text-sm font-semibold text-white mb-4">Threat Activity (Last 10 min)</h3>
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="critical" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="high" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="medium" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#eab308" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
            labelStyle={{ color: "#9ca3af" }}
            itemStyle={{ color: "#d1d5db" }}
          />
          <Area type="monotone" dataKey="medium" stroke="#eab308" strokeWidth={1.5} fill="url(#medium)" name="Medium" />
          <Area type="monotone" dataKey="high" stroke="#f97316" strokeWidth={1.5} fill="url(#high)" name="High" />
          <Area type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={2} fill="url(#critical)" name="Critical" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
