import { useEffect, useRef } from "react";
import { Package, Wifi, Link2, BellRing } from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";
import { useToast } from "../context/ToastContext";
import StatCard from "../components/StatCard";
import LiveBandwidthChart from "../components/LiveBandwidthChart";
import ProtocolChart from "../components/ProtocolChart";

function fmtBytes(b) {
  if (b >= 1_000_000) return (b / 1_000_000).toFixed(1) + " MB";
  if (b >= 1_000)     return (b / 1_000).toFixed(1) + " KB";
  return b + " B";
}

export default function Dashboard() {
  const { data, connected } = useWebSocket("/ws/live");
  const { addToast }  = useToast();
  const lastAlertId   = useRef(null);   // tracks the latest alert we've toasted
  const initialized   = useRef(false);  // skip the first frame (existing alerts)

  useEffect(() => {
    const alert = data?.latest_alert;
    if (!alert) return;

    if (!initialized.current) {
      // First WebSocket frame — record current alert so we don't toast it
      initialized.current  = true;
      lastAlertId.current  = alert.id;
      return;
    }

    if (alert.id === lastAlertId.current) return;
    lastAlertId.current = alert.id;
    addToast(alert);  // fire toast for any severity (aggregator only emits medium+)
  }, [data?.latest_alert?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Real-time network overview
          </p>
        </div>
        <div className={`flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border ${
          connected
            ? "bg-green-50 dark:bg-green-950/40 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800"
            : "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-500 animate-pulse" : "bg-gray-400"}`} />
          {connected ? "Live" : "Disconnected"}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Packets / sec"
          value={data?.packets_per_sec ?? "—"}
          icon={Package}
          color="blue"
        />
        <StatCard
          label="Bandwidth"
          value={data ? fmtBytes(data.bytes_per_sec) : "—"}
          unit="/s"
          icon={Wifi}
          color="green"
        />
        <StatCard
          label="Active connections"
          value={data?.active_connections ?? "—"}
          icon={Link2}
          color="amber"
        />
        <StatCard
          label="Unresolved alerts"
          value={data?.unresolved_alerts ?? "—"}
          icon={BellRing}
          color="red"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <LiveBandwidthChart
          bytesPerSec={data?.bytes_per_sec}
          packetsPerSec={data?.packets_per_sec}
        />
        <ProtocolChart protocols={data?.top_protocols ?? []} />
      </div>

      {/* Top talkers */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-4">
          Top Source IPs — last hour
        </p>
        {(data?.top_talkers_src ?? []).length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">
            Waiting for traffic data...
          </p>
        ) : (
          <div className="space-y-3">
            {data.top_talkers_src.map(({ ip, bytes }, i) => {
              const pct = Math.min(100, (bytes / (data.top_talkers_src[0]?.bytes || 1)) * 100);
              return (
                <div key={ip} className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-gray-400 dark:text-gray-500 w-4 text-right">
                    {i + 1}
                  </span>
                  <span className="font-mono text-sm text-gray-700 dark:text-gray-300 w-32 truncate">
                    {ip}
                  </span>
                  <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 w-20 text-right tabular-nums">
                    {fmtBytes(bytes)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
