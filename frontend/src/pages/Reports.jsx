import { useEffect, useState } from "react";
import { Download, FileText, BellRing, BarChart2, Link2,
         Package, Wifi, AlertTriangle, Activity } from "lucide-react";
import api from "../api/client";

// ── Config ────────────────────────────────────────────────────────────────────

const REPORT_TYPES = [
  {
    value: "traffic",
    label: "Traffic Log",
    icon:  BarChart2,
    desc:  "All captured packets with source, destination and protocol",
  },
  {
    value: "sessions",
    label: "Network Sessions",
    icon:  Link2,
    desc:  "Aggregated flows grouped by 5-tuple",
  },
  {
    value: "alerts",
    label: "Alert Summary",
    icon:  BellRing,
    desc:  "Security events and anomaly detections",
  },
  {
    value: "protocols",
    label: "Protocol Breakdown",
    icon:  FileText,
    desc:  "Bandwidth and packet count grouped by protocol",
  },
];

const TIME_RANGES = [
  { value: 1,   label: "Last 1 hour"  },
  { value: 6,   label: "Last 6 hours" },
  { value: 24,  label: "Last 24 hours"},
  { value: 72,  label: "Last 3 days"  },
  { value: 168, label: "Last 7 days"  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtBytes(b) {
  if (!b) return "0 B";
  if (b >= 1_000_000_000) return (b / 1_000_000_000).toFixed(2) + " GB";
  if (b >= 1_000_000)     return (b / 1_000_000).toFixed(1)     + " MB";
  if (b >= 1_000)         return (b / 1_000).toFixed(1)         + " KB";
  return b + " B";
}

function fmtNum(n) {
  if (n == null) return "—";
  return n.toLocaleString();
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SummaryCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800/60 rounded-lg px-4 py-3 flex items-center gap-3">
      <Icon size={16} className="text-blue-500 shrink-0" strokeWidth={1.75} />
      <div className="min-w-0">
        <p className="text-[11px] text-gray-400 dark:text-gray-500 uppercase tracking-wider font-medium">
          {label}
        </p>
        <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{value}</p>
        {sub && <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Reports() {
  const [reportType, setReportType] = useState("traffic");
  const [format,     setFormat]     = useState("csv");
  const [hours,      setHours]      = useState(24);
  const [loading,    setLoading]    = useState(false);
  const [summary,    setSummary]    = useState(null);
  const [sumLoading, setSumLoading] = useState(false);

  // Fetch preview stats whenever the time range changes
  useEffect(() => {
    setSumLoading(true);
    api.get("/reports/summary", { params: { hours } })
      .then((r) => setSummary(r.data))
      .catch(() => setSummary(null))
      .finally(() => setSumLoading(false));
  }, [hours]);

  const download = async () => {
    setLoading(true);
    try {
      const res = await api.get("/reports/export", {
        params: { report_type: reportType, format, hours },
        responseType: "blob",
      });
      const url  = window.URL.createObjectURL(res.data);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `${reportType}_${new Date().toISOString().slice(0, 10)}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">

      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Reports</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Export traffic data and analytics as CSV or JSON
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 items-start">

        {/* ── Left: export form ─────────────────────────────────── */}
        <div className="lg:col-span-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 shadow-sm space-y-6">

          {/* Report type */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">
              Report type
            </label>
            <div className="space-y-2">
              {REPORT_TYPES.map(({ value, label, icon: Icon, desc }) => (
                <button
                  key={value}
                  onClick={() => setReportType(value)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all ${
                    reportType === value
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800/60"
                  }`}
                >
                  <Icon
                    size={15}
                    strokeWidth={1.75}
                    className={reportType === value ? "text-blue-600 dark:text-blue-400" : "text-gray-400"}
                  />
                  <div>
                    <p className={`text-sm font-medium ${
                      reportType === value ? "text-blue-700 dark:text-blue-300" : "text-gray-700 dark:text-gray-300"
                    }`}>
                      {label}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Format + time range */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">
                Format
              </label>
              <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                {["csv", "json"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFormat(f)}
                    className={`flex-1 py-2 text-sm font-semibold uppercase transition-colors ${
                      format === f
                        ? "bg-blue-600 text-white"
                        : "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-2">
                Time range
              </label>
              <select
                value={hours}
                onChange={(e) => setHours(Number(e.target.value))}
                className="w-full text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TIME_RANGES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Download */}
          <button
            onClick={download}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-60 rounded-lg transition-colors shadow-sm"
          >
            <Download size={14} strokeWidth={2.5} />
            {loading ? "Generating report…" : `Download ${format.toUpperCase()}`}
          </button>
        </div>

        {/* ── Right: summary preview ──────────────────────────────── */}
        <div className="lg:col-span-2 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
            Preview — {TIME_RANGES.find((t) => t.value === hours)?.label}
          </p>

          {sumLoading ? (
            <div className="h-48 flex items-center justify-center">
              <Activity size={20} className="text-blue-500 animate-spin" />
            </div>
          ) : summary ? (
            <div className="grid grid-cols-1 gap-2">
              <SummaryCard
                icon={Package}
                label="Packets captured"
                value={fmtNum(summary.total_packets)}
              />
              <SummaryCard
                icon={Wifi}
                label="Total volume"
                value={fmtBytes(summary.total_bytes)}
              />
              <SummaryCard
                icon={Link2}
                label="Sessions"
                value={fmtNum(summary.total_sessions)}
              />
              <SummaryCard
                icon={AlertTriangle}
                label="Alerts"
                value={fmtNum(summary.total_alerts)}
                sub={summary.unresolved_alerts > 0 ? `${summary.unresolved_alerts} unresolved` : "all resolved"}
              />
              <SummaryCard
                icon={BarChart2}
                label="Top protocol"
                value={summary.top_protocol ?? "—"}
              />
            </div>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 py-8 text-center">
              No data for this period
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
