import { Globe, AlertTriangle, Search, X } from "lucide-react";
import { useState, useMemo } from "react";
import type { LiveConnection, ConnectionStats } from "../types";

interface Props {
  connections: LiveConnection[];
  stats: ConnectionStats | null;
}

function getRowStyle(c: LiveConnection) {
  if (c.is_malicious_ip) return "bg-rose-50 border-l-2 border-rose-400";
  if (c.is_suspicious)   return "bg-amber-50 border-l-2 border-amber-400";
  return "";
}

export function ConnectionsPanel({ connections, stats }: Props) {
  const [search, setSearch] = useState("");
  const [showOnlySuspicious, setShowOnlySuspicious] = useState(false);

  const filtered = useMemo(() => {
    let list = connections;
    if (showOnlySuspicious) list = list.filter(c => c.is_suspicious || c.is_malicious_ip);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(c =>
        c.remote_ip.includes(q) ||
        c.hostname.toLowerCase().includes(q) ||
        c.process_name.toLowerCase().includes(q) ||
        c.country_name.toLowerCase().includes(q) ||
        c.protocol.toLowerCase().includes(q)
      );
    }
    return list;
  }, [connections, search, showOnlySuspicious]);

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Globe className="w-4 h-4 text-sky-600 shrink-0" />
        <h2 className="section-title">Live Connections</h2>
        <span className="ml-auto flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-500">
            {stats?.total ?? 0} connections · {stats?.unique_remote_ips ?? 0} unique IPs
          </span>
          {(stats?.suspicious ?? 0) > 0 && (
            <span className="badge-high flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {stats!.suspicious} suspicious
            </span>
          )}
        </span>
      </div>

      {/* Top-process chips */}
      {stats?.top_processes && stats.top_processes.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {stats.top_processes.slice(0, 6).map(p => (
            <button
              key={p.name}
              onClick={() => setSearch(p.name)}
              className="text-xs bg-slate-100 border border-slate-200 rounded-full px-2.5 py-0.5 hover:bg-sky-50 hover:border-sky-200 hover:text-sky-700 transition-colors"
            >
              {p.name.replace(".exe", "")} <span className="text-slate-400">{p.count}</span>
            </button>
          ))}
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-2 mb-3">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Filter by IP, host, process, country..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-7 pr-7 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-300"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2">
              <X className="w-3 h-3 text-slate-400" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowOnlySuspicious(v => !v)}
          className={`text-xs px-2.5 py-1.5 rounded-lg border transition-colors whitespace-nowrap ${
            showOnlySuspicious
              ? "bg-rose-600 text-white border-rose-600"
              : "border-slate-200 text-slate-600 hover:border-rose-300 hover:text-rose-700"
          }`}
        >
          Suspicious only
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left py-2 pr-3 text-slate-400 font-medium">Process</th>
              <th className="text-left py-2 pr-3 text-slate-400 font-medium">Destination</th>
              <th className="text-left py-2 pr-3 text-slate-400 font-medium">Country</th>
              <th className="text-left py-2 pr-3 text-slate-400 font-medium">Protocol</th>
              <th className="text-left py-2 text-slate-400 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-400">
                  {connections.length === 0 ? "Waiting for connection data..." : "No matches"}
                </td>
              </tr>
            ) : (
              filtered.slice(0, 50).map((c, i) => (
                <tr
                  key={i}
                  className={`border-b border-slate-50 hover:bg-slate-50/80 ${getRowStyle(c)}`}
                >
                  <td className="py-1.5 pr-3 font-mono text-slate-700">
                    {c.process_name.replace(".exe", "")}
                  </td>
                  <td className="py-1.5 pr-3 max-w-[180px]">
                    <div className="truncate font-mono text-slate-600" title={c.hostname}>
                      {c.hostname !== c.remote_ip ? c.hostname : c.remote_ip}
                    </div>
                    <div className="text-slate-400 truncate">{c.remote_ip}:{c.remote_port}</div>
                  </td>
                  <td className="py-1.5 pr-3 whitespace-nowrap">
                    <span title={`${c.city ? c.city + ", " : ""}${c.country_name}${c.isp ? " · " + c.isp : ""}`}>
                      {c.flag} {c.country || "??"}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 font-mono text-sky-700">{c.protocol}</td>
                  <td className="py-1.5">
                    {c.is_malicious_ip ? (
                      <span className="text-xs font-semibold text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded">
                        MALICIOUS
                      </span>
                    ) : c.is_high_risk_country ? (
                      <span className="text-xs text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                        High-risk
                      </span>
                    ) : c.is_suspicious_isp ? (
                      <span className="text-xs text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                        VPS/Hosting
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {filtered.length > 50 && (
          <p className="text-center text-xs text-slate-400 py-2">
            Showing 50 of {filtered.length} — use the filter to narrow down
          </p>
        )}
      </div>

      {/* Country breakdown */}
      {stats?.top_countries && stats.top_countries.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
          {stats.top_countries.slice(0, 10).map(c => (
            <button
              key={c.code}
              onClick={() => setSearch(c.code)}
              className="text-xs text-slate-500 hover:text-sky-700 transition-colors"
            >
              {c.code} <span className="text-slate-300">{c.count}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
