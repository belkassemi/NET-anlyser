import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Monitor, Link2, Bell, FileBarChart2,
  Settings, Sun, Moon, LogOut, Activity,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../context/ThemeContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/devices",   label: "Devices",   icon: Monitor },
  { to: "/sessions",  label: "Sessions",  icon: Link2 },
  { to: "/alerts",    label: "Alerts",    icon: Bell },
  { to: "/reports",   label: "Reports",   icon: FileBarChart2 },
  { to: "/settings",  label: "Settings",  icon: Settings },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="w-56 shrink-0 flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800">

        {/* Brand */}
        <div className="h-14 flex items-center gap-2.5 px-5 border-b border-gray-200 dark:border-gray-800">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
            <Activity size={14} className="text-white" strokeWidth={2.5} />
          </div>
          <span className="font-semibold text-gray-900 dark:text-white tracking-tight">
            NetAnalyzer
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} strokeWidth={isActive ? 2.5 : 1.75} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-800 p-2 space-y-0.5">
          {/* Theme toggle */}
          <button
            onClick={toggle}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            {theme === "dark"
              ? <Sun size={16} strokeWidth={1.75} />
              : <Moon size={16} strokeWidth={1.75} />
            }
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>

          {/* User info */}
          <div className="px-3 py-2">
            <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
              {user?.email}
            </p>
            <p className="text-[11px] text-gray-400 dark:text-gray-500 capitalize mt-0.5">
              {user?.role}
            </p>
          </div>

          {/* Logout */}
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors"
          >
            <LogOut size={16} strokeWidth={1.75} />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
