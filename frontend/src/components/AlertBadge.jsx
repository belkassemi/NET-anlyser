const STYLES = {
  critical: "bg-red-100    dark:bg-red-950/60  text-red-700   dark:text-red-400   border-red-200   dark:border-red-800",
  high:     "bg-orange-100 dark:bg-orange-950/60 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-800",
  medium:   "bg-amber-100  dark:bg-amber-950/60 text-amber-700  dark:text-amber-400  border-amber-200  dark:border-amber-800",
  low:      "bg-blue-100   dark:bg-blue-950/60  text-blue-700  dark:text-blue-400   border-blue-200   dark:border-blue-800",
};

export default function AlertBadge({ severity }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border ${STYLES[severity] ?? STYLES.low}`}>
      {severity}
    </span>
  );
}
