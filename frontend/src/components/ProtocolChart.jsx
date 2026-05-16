import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { useTheme } from "../context/ThemeContext";

const PALETTE = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-gray-900 dark:text-white">{payload[0].name}</p>
      <p className="text-gray-500 dark:text-gray-400">{payload[0].value} packets</p>
    </div>
  );
}

export default function ProtocolChart({ protocols = [] }) {
  const { isDark } = useTheme();
  const legendColor = isDark ? "#6b7280" : "#9ca3af";
  const data = protocols.map((p) => ({ name: p.protocol, value: p.count }));

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-4">
        Protocol Distribution
      </p>
      {data.length === 0 ? (
        <div className="h-44 flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">
          Waiting for traffic data...
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data} cx="50%" cy="50%"
              innerRadius={52} outerRadius={78}
              dataKey="value" paddingAngle={3}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              iconType="circle" iconSize={8}
              wrapperStyle={{ fontSize: 12, color: legendColor }}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
