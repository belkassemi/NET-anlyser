import { useState } from "react";
import { UserPlus, CheckCircle, XCircle } from "lucide-react";
import api from "../api/client";
import { useAuth } from "../hooks/useAuth";

const ROLES = [
  { value: "viewer",  label: "Viewer",  desc: "Read-only access" },
  { value: "analyst", label: "Analyst", desc: "Read & write on traffic and alerts" },
  { value: "admin",   label: "Admin",   desc: "Full access including user management" },
];

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}
      </label>
      {children}
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [role,     setRole]     = useState("viewer");
  const [status,   setStatus]   = useState(null); // { ok, msg }

  const inputCls =
    "w-full px-3.5 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition";

  const createUser = async (e) => {
    e.preventDefault();
    setStatus(null);
    try {
      await api.post("/auth/register", { email, password, role });
      setStatus({ ok: true, msg: `User "${email}" created successfully.` });
      setEmail(""); setPassword("");
    } catch (err) {
      setStatus({ ok: false, msg: err.response?.data?.detail ?? "Failed to create user." });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Account and user management</p>
      </div>

      {/* Current user */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm max-w-xl">
        <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">
          Current session
        </p>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
            {user?.email?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-white">{user?.email}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 capitalize mt-0.5">{user?.role}</p>
          </div>
        </div>
      </div>

      {/* Create user — admin only */}
      {user?.role === "admin" && (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 shadow-sm max-w-xl">
          <div className="flex items-center gap-2 mb-5">
            <UserPlus size={16} className="text-gray-400" strokeWidth={1.75} />
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">Create new user</p>
          </div>

          <form onSubmit={createUser} className="space-y-4">
            <Field label="Email">
              <input
                type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                className={inputCls}
              />
            </Field>

            <Field label="Password">
              <input
                type="password" required value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputCls}
              />
            </Field>

            <Field label="Role">
              <div className="space-y-2">
                {ROLES.map(({ value, label, desc }) => (
                  <label
                    key={value}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      role === value
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40"
                        : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                    }`}
                  >
                    <input
                      type="radio" name="role" value={value}
                      checked={role === value}
                      onChange={() => setRole(value)}
                      className="accent-blue-600"
                    />
                    <div>
                      <p className={`text-sm font-medium ${role === value ? "text-blue-700 dark:text-blue-300" : "text-gray-700 dark:text-gray-300"}`}>
                        {label}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500">{desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </Field>

            {status && (
              <div className={`flex items-start gap-2.5 px-3.5 py-3 rounded-lg border text-sm ${
                status.ok
                  ? "bg-green-50 dark:bg-green-950/40 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400"
                  : "bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400"
              }`}>
                {status.ok
                  ? <CheckCircle size={15} className="shrink-0 mt-0.5" />
                  : <XCircle    size={15} className="shrink-0 mt-0.5" />}
                {status.msg}
              </div>
            )}

            <button
              type="submit"
              className="w-full py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
            >
              Create user
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
