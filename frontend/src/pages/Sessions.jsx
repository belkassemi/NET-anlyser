import { useEffect, useState } from "react";
import api from "../api/client";
import DataTable from "../components/DataTable";

function fmtBytes(b) {
  if (b >= 1_000_000) return (b / 1_000_000).toFixed(1) + " MB";
  if (b >= 1_000)     return (b / 1_000).toFixed(1) + " KB";
  return b + " B";
}

const PROTOCOLS = ["TCP", "UDP", "ICMP", "DNS", "HTTP", "HTTPS", "ARP"];

const COLUMNS = [
  {
    key: "src", label: "Source",
    render: (r) => (
      <span className="font-mono text-xs">
        {r.src_ip}<span className="text-gray-400">:{r.src_port ?? "*"}</span>
      </span>
    ),
  },
  {
    key: "dst", label: "Destination",
    render: (r) => (
      <span className="font-mono text-xs">
        {r.dst_ip}<span className="text-gray-400">:{r.dst_port ?? "*"}</span>
      </span>
    ),
  },
  {
    key: "protocol", label: "Protocol",
    render: (r) => (
      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
        {r.protocol}
      </span>
    ),
  },
  { key: "layer7_category", label: "Application" },
  { key: "bytes",   label: "Volume",   render: (r) => fmtBytes(r.bytes) },
  { key: "packets", label: "Packets" },
  { key: "duration", label: "Duration", render: (r) => `${(r.duration ?? 0).toFixed(1)}s` },
  {
    key: "start_time", label: "Started",
    render: (r) => (
      <span className="text-xs text-gray-400 dark:text-gray-500">
        {new Date(r.start_time).toLocaleTimeString()}
      </span>
    ),
  },
];

export default function Sessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [protocol, setProtocol] = useState("");
  const [page, setPage]         = useState(0);
  const pageSize = 50;

  useEffect(() => {
    setLoading(true);
    const params = {
      limit: pageSize,
      offset: page * pageSize
    };
    if (protocol) params.protocol = protocol;

    api.get("/sessions", { params })
      .then((r) => setSessions(r.data))
      .finally(() => setLoading(false));
  }, [protocol, page]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Sessions</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Aggregated network flows
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={protocol}
            onChange={(e) => { setProtocol(e.target.value); setPage(0); }}
            className="text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
          >
            <option value="">All protocols</option>
            {PROTOCOLS.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      <div className="relative">
        {loading && (
          <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-xl">
             <span className="text-sm font-medium text-blue-500 animate-pulse">Refreshing data...</span>
          </div>
        )}
        
        <DataTable
          columns={COLUMNS}
          rows={sessions}
          keyFn={(r) => r.id}
          emptyText="No sessions recorded yet."
        />
      </div>

      <div className="flex items-center justify-between bg-white dark:bg-gray-900 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div className="text-sm text-gray-500">
          Showing <span className="font-medium text-gray-900 dark:text-white">{sessions.length}</span> results on page {page + 1}
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
            disabled={sessions.length < pageSize}
            className="px-4 py-1.5 text-sm font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
