import { useEffect, useState } from "react";
import { AlertCircle, X, ShieldAlert, Zap } from "lucide-react";

const SEVERITY_STYLES = {
  critical: "bg-red-50 border-red-200 text-red-800 dark:bg-red-950/40 dark:border-red-900/50",
  high: "bg-orange-50 border-orange-200 text-orange-800 dark:bg-orange-950/40 dark:border-orange-900/50",
  medium: "bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/40 dark:border-amber-900/50",
  low: "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950/40 dark:border-blue-900/50",
};

const BAR_COLORS = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-amber-500",
  low: "bg-blue-500",
};

export default function Toast({ alert, onClose }) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const duration = 6000; // 6 seconds
    const interval = 10;
    const step = (interval / duration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev <= 0) {
          clearInterval(timer);
          onClose();
          return 0;
        }
        return prev - step;
      });
    }, interval);

    return () => clearInterval(timer);
  }, [onClose]);

  return (
    <div
      className={`w-80 p-4 rounded-xl border shadow-2xl backdrop-blur-md animate-in slide-in-from-right-full duration-300 relative overflow-hidden ${SEVERITY_STYLES[alert.severity]}`}
    >
      <div className="flex gap-3">
        <div className="shrink-0 mt-0.5">
          {alert.severity === "critical" ? (
            <ShieldAlert className="text-red-500" size={18} />
          ) : (
            <AlertCircle className={BAR_COLORS[alert.severity].replace('bg-', 'text-')} size={18} />
          )}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-xs font-bold uppercase tracking-wider opacity-80">
              {alert.severity} Alert
            </span>
            <button onClick={onClose} className="opacity-40 hover:opacity-100 transition-opacity">
              <X size={14} />
            </button>
          </div>
          <p className="text-sm font-semibold truncate mb-1">
            {alert.type.replace(/_/g, " ")}
          </p>
          <p className="text-xs opacity-90 leading-snug">
            {alert.message}
          </p>
          {alert.src_ip && (
            <div className="mt-2 text-[10px] font-mono opacity-60">
              Source: {alert.src_ip}
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="absolute bottom-0 left-0 h-1 w-full bg-black/5 dark:bg-white/5">
        <div
          className={`h-full transition-all linear ${BAR_COLORS[alert.severity]}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
