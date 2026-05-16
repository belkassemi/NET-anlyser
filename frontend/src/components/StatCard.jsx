const COLORS = {
  blue:   "bg-blue-50   dark:bg-blue-950/40   text-blue-600   dark:text-blue-400",
  green:  "bg-green-50  dark:bg-green-950/40  text-green-600  dark:text-green-400",
  amber:  "bg-amber-50  dark:bg-amber-950/40  text-amber-600  dark:text-amber-400",
  red:    "bg-red-50    dark:bg-red-950/40    text-red-600    dark:text-red-400",
};

export default function StatCard({ label, value, unit = "", icon: Icon, color = "blue" }) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
          {label}
        </span>
        {Icon && (
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${COLORS[color]}`}>
            <Icon size={15} strokeWidth={2} />
          </div>
        )}
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white leading-none">
        {value}
        {unit && (
          <span className="text-sm font-normal text-gray-400 dark:text-gray-500 ml-1.5">
            {unit}
          </span>
        )}
      </p>
    </div>
  );
}
