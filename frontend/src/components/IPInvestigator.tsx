import {
  Search,
  Shield,
  ShieldAlert,
  ShieldX,
  Wifi,
  WifiOff,
  Globe,
  Server,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Activity,
  Lock,
  Unlock,
} from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import type { IPInvestigationResult } from "../types";

const RISK_CONFIG = {
  none:     { color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200", Icon: CheckCircle2, label: "Clean" },
  low:      { color: "text-sky-700",     bg: "bg-sky-50 border-sky-200",         Icon: Shield,       label: "Low Risk" },
  medium:   { color: "text-yellow-700",  bg: "bg-yellow-50 border-yellow-200",   Icon: ShieldAlert,  label: "Medium Risk" },
  high:     { color: "text-amber-700",   bg: "bg-amber-50 border-amber-200",     Icon: ShieldAlert,  label: "High Risk" },
  critical: { color: "text-rose-700",    bg: "bg-rose-50 border-rose-200",       Icon: ShieldX,      label: "Critical" },
};

const PORT_RISK_COLORS: Record<string, string> = {
  none:     "text-emerald-700 bg-emerald-50",
  low:      "text-sky-700 bg-sky-50",
  medium:   "text-yellow-700 bg-yellow-50",
  high:     "text-amber-700 bg-amber-50",
  critical: "text-rose-700 bg-rose-50",
};

function isValidIP(ip: string): boolean {
  const parts = ip.trim().split(".");
  if (parts.length !== 4) return false;
  return parts.every(p => /^\d+$/.test(p) && parseInt(p) <= 255);
}

export function IPInvestigator() {
  const [query,   setQuery]   = useState("");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState<IPInvestigationResult | null>(null);
  const [error,   setError]   = useState<string | null>(null);

  const handleInvestigate = async () => {
    const ip = query.trim();
    if (!isValidIP(ip)) {
      setError("Please enter a valid IPv4 address (e.g. 192.168.1.1 or 8.8.8.8)");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.investigateIP(ip);
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Investigation failed");
    } finally {
      setLoading(false);
    }
  };

  const risk   = result ? (RISK_CONFIG[result.risk_level as keyof typeof RISK_CONFIG] ?? RISK_CONFIG.none) : null;
  const RiskIcon = risk?.Icon;

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Search className="w-4 h-4 text-sky-600" />
        <h2 className="section-title">IP Investigator</h2>
        <span className="muted ml-auto">Enter any IP to investigate</span>
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="e.g. 192.168.1.1 or 8.8.8.8"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !loading && handleInvestigate()}
          className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-300 font-mono"
          disabled={loading}
        />
        <button
          onClick={handleInvestigate}
          disabled={loading || !query.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-sky-600 rounded-lg hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shrink-0"
        >
          {loading ? (
            <Activity className="w-4 h-4 animate-pulse" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          {loading ? "Investigating..." : "Investigate"}
        </button>
      </div>

      {/* Quick-pick common IPs */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {["192.168.1.1", "8.8.8.8", "1.1.1.1"].map(ip => (
          <button
            key={ip}
            onClick={() => { setQuery(ip); }}
            className="text-xs font-mono text-slate-500 bg-slate-100 hover:bg-sky-50 hover:text-sky-700 border border-slate-200 rounded-full px-2.5 py-0.5 transition-colors"
          >
            {ip}
          </button>
        ))}
        <span className="text-xs text-slate-400 self-center">quick-pick</span>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          <p className="text-xs text-rose-700">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 bg-slate-100 rounded-lg" />
          ))}
        </div>
      )}

      {/* Results */}
      {result && risk && RiskIcon && !loading && (
        <div className="space-y-4">
          {/* Summary banner */}
          <div className={`flex items-center gap-3 border rounded-xl px-4 py-3 ${risk.bg}`}>
            <RiskIcon className={`w-6 h-6 ${risk.color} shrink-0`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-base font-bold text-slate-800">{result.ip}</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${risk.bg} ${risk.color}`}>
                  {risk.label}
                </span>
                {result.flag && (
                  <span className="text-lg">{result.flag}</span>
                )}
              </div>
              <p className="text-xs text-slate-600 truncate mt-0.5">
                {result.hostname !== result.ip ? result.hostname : result.country_name || "Private Network"}
              </p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {result.is_alive ? (
                <span className="flex items-center gap-1 text-xs text-emerald-700">
                  <Wifi className="w-3.5 h-3.5" />
                  {result.latency_ms != null ? `${result.latency_ms}ms` : "Online"}
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs text-slate-500">
                  <WifiOff className="w-3.5 h-3.5" /> Offline
                </span>
              )}
            </div>
          </div>

          {/* Details grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Geo / Network info */}
            <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
              <div className="flex items-center gap-1.5 mb-2">
                <Globe className="w-3.5 h-3.5 text-sky-600" />
                <span className="text-xs font-semibold text-slate-700">
                  {result.is_private ? "Local Network" : "Geolocation"}
                </span>
              </div>
              <div className="space-y-1.5">
                {result.is_private ? (
                  <Row label="Type" value="Private / LAN IP" />
                ) : (
                  <>
                    <Row label="Country" value={`${result.flag} ${result.country_name}`} />
                    {result.city     && <Row label="City"   value={result.city} />}
                    {result.isp      && <Row label="ISP"    value={result.isp} />}
                    {result.org      && result.org !== result.isp && <Row label="Org" value={result.org} />}
                    {result.is_high_risk_country && (
                      <p className="text-xs text-amber-700 font-medium">⚠ High-risk country</p>
                    )}
                    {result.is_suspicious_isp && (
                      <p className="text-xs text-amber-700 font-medium">⚠ VPS / hosting ISP</p>
                    )}
                  </>
                )}
                {result.hostname !== result.ip && (
                  <Row label="Hostname" value={result.hostname} mono />
                )}
              </div>
            </div>

            {/* Threat intel */}
            <div className={`rounded-lg p-3 border ${result.is_malicious ? "bg-rose-50 border-rose-200" : "bg-slate-50 border-slate-100"}`}>
              <div className="flex items-center gap-1.5 mb-2">
                <Shield className={`w-3.5 h-3.5 ${result.is_malicious ? "text-rose-600" : "text-emerald-600"}`} />
                <span className="text-xs font-semibold text-slate-700">Threat Intelligence</span>
              </div>
              {result.is_malicious && result.threat_details ? (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-rose-700">MALICIOUS IP DETECTED</p>
                  <Row label="Threat"  value={(result.threat_details as Record<string,string>).threat ?? "Unknown"} />
                  <Row label="Source"  value={result.threat_source} />
                  {(result.threat_details as Record<string,number>).confidence && (
                    <Row label="Confidence" value={`${Math.round(((result.threat_details as Record<string,number>).confidence ?? 0) * 100)}%`} />
                  )}
                </div>
              ) : (
                <div className="space-y-1.5">
                  <p className="text-xs text-emerald-700 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> No known threats
                  </p>
                  <Row label="Source" value={result.threat_source} />
                </div>
              )}
            </div>
          </div>

          {/* Registered device (if any) */}
          {result.registered_device && (
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <Server className="w-3.5 h-3.5 text-sky-600" />
                <span className="text-xs font-semibold text-slate-700">Registered Device</span>
              </div>
              <div className="space-y-1.5">
                <Row label="Name"   value={result.registered_device.name} />
                <Row label="Type"   value={result.registered_device.type} />
                {result.registered_device.mac && <Row label="MAC" value={result.registered_device.mac} mono />}
                <Row label="Status" value={result.registered_device.status} />
              </div>
            </div>
          )}

          {/* Open ports (LAN scan) */}
          {result.open_ports.length > 0 && (
            <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
              <div className="flex items-center gap-1.5 mb-2">
                <Lock className="w-3.5 h-3.5 text-slate-600" />
                <span className="text-xs font-semibold text-slate-700">
                  Open Ports ({result.open_ports.length})
                </span>
                {result.dangerous_ports.length > 0 && (
                  <span className="ml-auto text-xs text-rose-700 font-semibold">
                    {result.dangerous_ports.length} dangerous
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {result.open_ports.map(p => (
                  <span
                    key={p.port}
                    className={`text-xs font-mono px-2 py-0.5 rounded border ${PORT_RISK_COLORS[p.risk] ?? PORT_RISK_COLORS.low}`}
                    title={p.risk}
                  >
                    {p.port} <span className="font-sans opacity-75">{p.service}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* No open ports */}
          {result.is_private && result.open_ports.length === 0 && result.is_alive && (
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              <Unlock className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <p className="text-xs text-emerald-700">No common dangerous ports open</p>
            </div>
          )}

          {/* Active connections */}
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
            <div className="flex items-center gap-1.5 mb-2">
              <Activity className="w-3.5 h-3.5 text-slate-600" />
              <span className="text-xs font-semibold text-slate-700">
                Active Connections ({result.connection_count})
              </span>
            </div>
            {result.active_connections.length === 0 ? (
              <p className="text-xs text-slate-400">No active connections to this IP right now</p>
            ) : (
              <div className="space-y-1.5">
                {result.active_connections.slice(0, 8).map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-sky-700 shrink-0">{c.protocol}</span>
                    <span className="text-slate-600 font-mono">{c.remote_ip}:{c.remote_port}</span>
                    <span className="text-slate-400 truncate">{c.process_name?.replace(".exe","")}</span>
                  </div>
                ))}
                {result.active_connections.length > 8 && (
                  <p className="text-xs text-slate-400">
                    +{result.active_connections.length - 8} more connections
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Scan time */}
          <p className="text-xs text-slate-400 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Scanned {new Date(result.scanned_at).toLocaleTimeString()}
          </p>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="text-center py-8 border-2 border-dashed border-slate-200 rounded-xl">
          <Globe className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-500 font-medium">Enter an IP address above</p>
          <p className="text-xs text-slate-400 mt-1">
            Works for both LAN devices (192.168.x.x) and public IPs
          </p>
        </div>
      )}
    </div>
  );
}

// Helper row component
function Row({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-xs text-slate-500 shrink-0">{label}</span>
      <span className={`text-xs text-slate-700 truncate text-right ${mono ? "font-mono" : ""}`} title={value}>
        {value}
      </span>
    </div>
  );
}
