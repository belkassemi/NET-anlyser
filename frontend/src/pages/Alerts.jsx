import { useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import api from "../api/client";
import DataTable from "../components/DataTable";
import AlertBadge from "../components/AlertBadge";

export default function Alerts() {
  const [alerts,       setAlerts]       = useState([]);
  const [loading,      setLoading]      = useState(true);
  const [showResolved, setShowResolved] = useState(false);
  const [severity,     setSeverity]     = useState("");
  const [page,         setPage]         = useState(0);
  const pageSize = 50;

  const load = () => {
    setLoading(true);
    const params = {
      limit: pageSize,
      offset: page * pageSize
    };
    if (!showResolved) params.resolved = false;
    if (severity)      params.severity = severity;
    api.get("/alerts", { params })
      .then((r) => setAlerts(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [showResolved, severity, page]);

  const resolve = async (id) => {
    await api.patch(`/alerts/${id}`, { resolved: true });
    setAlerts((prev) =>
      showResolved
        ? prev.map((a) => a.id === id ? { ...a, resolved: true } : a)
        : prev.filter((a) => a.id !== id)
    );
  };

  const COLUMNS = [
    { key: "severity", label: "Severity", render: (r) => <AlertBadge severity={r.severity} /> },
    {
      key: "type", label: "Type",
      render: (r) => (
        <span className="text-gray-700 dark:text-gray-300 capitalize">
          {r.type.replace(/_/g, " ")}
        </span>
      ),
    },
    { key: "message", label: "Message" },
    {
      key: "src_ip", label: "Source IP",
      render: (r) => (
        <span className="font-mono text-xs text-gray-500 dark:text-gray-400">{r.src_ip ?? "—"}</span>
      ),
    },
    {
      key: "created_at", label: "Time",
      render: (r) => (
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {new Date(r.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: "action", label: "",
      render: (r) => !r.resolved ? (
        <button
          onClick={() => resolve(r.id)}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
        >
          <CheckCircle2 size={13} />
          Resolve
        </button>
      ) : (
        <span className="text-xs text-gray-400 dark:text-gray-600">Resolved</span>
      ),
    },
  ];

  const unresolved = alerts.filter((a) => !a.resolved).length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Alerts</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Security & anomaly events</p>
          </div>
          {unresolved > 0 && (
            <span className="px-2 py-0.5 bg-red-600 text-white text-xs font-bold rounded-full">
              {unresolved}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All severities</option>
            {["critical", "high", "medium", "low"].map((s) => (
              <option key={s} value={s} className="capitalize">{s}</option>
            ))}
          </select>

          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 accent-blue-600"
            />
            Show resolved
          </label>
        </div>
      </div>

      <div className="relative">
        {loading && (
          <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-xl">
             <span className="text-sm font-medium text-blue-500 animate-pulse">Updating...</span>
          </div>
        )}
        <DataTable
          columns={COLUMNS}
          rows={alerts}
          keyFn={(r) => r.id}
          emptyText="No alerts found."
        />
      </div>

      <div className="flex items-center justify-between bg-white dark:bg-gray-900 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div className="text-sm text-gray-500">
          Showing <span className="font-medium text-gray-900 dark:text-white">{alerts.length}</span> results on page {page + 1}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-4 py-1.5 text-sm font-medium bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={alerts.length < pageSize}
            className="px-4 py-1.5 text-sm font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
