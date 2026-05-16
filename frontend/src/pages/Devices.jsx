import { useEffect, useState } from "react";
import { Monitor, RefreshCw } from "lucide-react";
import api from "../api/client";
import DataTable from "../components/DataTable";

const COLUMNS = [
  {
    key: "ip", label: "IP Address",
    render: (r) => <span className="font-mono text-sm">{r.ip}</span>,
  },
  { key: "mac",      label: "MAC Address" },
  { key: "hostname", label: "Hostname" },
  { key: "vendor",   label: "Vendor" },
  {
    key: "status", label: "Status",
    render: (r) => (
      <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${
        r.status
          ? "bg-green-50 dark:bg-green-950/40 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800"
          : "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-500 border-gray-200 dark:border-gray-700"
      }`}>
        <span className={`w-1.5 h-1.5 rounded-full ${r.status ? "bg-green-500" : "bg-gray-400"}`} />
        {r.status ? "Online" : "Offline"}
      </span>
    ),
  },
  {
    key: "last_seen", label: "Last Seen",
    render: (r) => (
      <span className="text-gray-400 dark:text-gray-500 text-xs">
        {new Date(r.last_seen).toLocaleString()}
      </span>
    ),
  },
];

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const load = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const r = await api.get("/devices", { 
        params: { limit: pageSize, offset: page * pageSize } 
      });
      setDevices(r.data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(() => load(), 10_000);
    return () => clearInterval(id);
  }, [page]);

  const online  = devices.filter((d) => d.status).length;
  const offline = devices.length - online;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">Devices</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Discovered network hosts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
              {online} online
            </span>
            <span className="text-gray-400 dark:text-gray-500">{offline} offline</span>
          </div>
          <button
            onClick={() => load(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>
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
          rows={devices}
          keyFn={(r) => r.id}
          emptyText="No devices discovered yet. Start the capture service to detect hosts."
        />
      </div>

      <div className="flex items-center justify-between bg-white dark:bg-gray-900 p-4 rounded-xl border border-gray-100 dark:border-gray-800 shadow-sm">
        <div className="text-sm text-gray-500">
          Showing <span className="font-medium text-gray-900 dark:text-white">{devices.length}</span> results on page {page + 1}
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
            disabled={devices.length < pageSize}
            className="px-4 py-1.5 text-sm font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
