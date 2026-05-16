import { useEffect, useRef, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { useTheme } from "../context/ThemeContext";

const MAX_POINTS = 60;

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="text-gray-900 dark:text-white font-medium">{payload[0]?.value} KB/s</p>
    </div>
  );
}

export default function LiveBandwidthChart({ bytesPerSec, packetsPerSec }) {
  const [history, setHistory] = useState([]);
  const tick = useRef(0);
  const { isDark } = useTheme();

  useEffect(() => {
    if (bytesPerSec == null) return;
    tick.current += 1;
    setHistory((prev) =>
      [...prev, { t: tick.current, bytes: Math.round(bytesPerSec / 1024), packets: Math.round(packetsPerSec) }].slice(-MAX_POINTS)
    );
  }, [bytesPerSec, packetsPerSec]);

  const gridColor  = isDark ? "#1f2937" : "#f3f4f6";
  const axisColor  = isDark ? "#4b5563" : "#9ca3af";

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-4">
        Live Bandwidth
      </p>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={history} margin={{ top: 4, right: 4, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="bwFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis dataKey="t" hide />
          <YAxis stroke={axisColor} tick={{ fill: axisColor, fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone" dataKey="bytes"
            stroke="#3b82f6" fill="url(#bwFill)"
            strokeWidth={2} dot={false} activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
