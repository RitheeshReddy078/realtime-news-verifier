import { useState } from "react";

import {
  LayoutDashboard,
  ScanSearch,
  History,
  Activity,
  ShieldCheck,
  Settings,
  Newspaper,
  Menu,
  X,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Verify News", icon: ScanSearch, path: "/verify" },
  { label: "History", icon: History, path: "/history" },
  { label: "System Status", icon: Activity, path: "/status" },
];

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);

  const closeSidebar = () => setIsOpen(false);

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsOpen(true)}
        aria-label="Open navigation menu"
        className="fixed left-4 top-5 z-50 rounded-lg border border-slate-700
        bg-[#111C2D] p-2 text-slate-300 shadow-lg
        transition hover:bg-slate-800 md:hidden"
      >
        <Menu size={21} />
      </button>

      {/* Mobile background overlay */}
      {isOpen && (
        <button
          onClick={closeSidebar}
          aria-label="Close navigation menu"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-64 flex-col
        border-r border-slate-800 bg-[#0D1625]
        transition-transform duration-300 ease-in-out
        ${
          isOpen
            ? "translate-x-0"
            : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Logo and Branding */}
        <div className="flex h-20 shrink-0 items-center justify-between gap-3 border-b border-slate-800 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-400">
              <ShieldCheck size={24} />
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-wide text-white">
                TruthLens
              </h1>

              <p className="text-xs text-slate-500">
                AI News Intelligence
              </p>
            </div>
          </div>

          {/* Mobile close button */}
          <button
            onClick={closeSidebar}
            aria-label="Close sidebar"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
          >
            <X size={20} />
          </button>
        </div>

        {/* Main Navigation */}
        <div className="px-5 pt-8">
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
            Workspace
          </p>

          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;

              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  end={item.path === "/"}
                  onClick={closeSidebar}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${
                      isActive
                        ? "border border-cyan-400/20 bg-cyan-400/10 font-semibold text-cyan-300"
                        : "text-slate-400 hover:bg-slate-800 hover:text-white"
                    }`
                  }
                >
                  <Icon size={19} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section */}
        <div className="mt-auto border-t border-slate-800 p-5">

          {/* Workspace Information */}
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-slate-800/60 p-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/15 text-violet-300">
              <Newspaper size={19} />
            </div>

            <div>
              <p className="text-sm font-medium text-white">
                News Intelligence
              </p>

              <p className="text-xs text-slate-500">
                Verification workspace
              </p>
            </div>
          </div>

          {/* Settings Navigation */}
          <NavLink
            to="/settings"
            onClick={closeSidebar}
            className={({ isActive }) =>
              `flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                isActive
                  ? "bg-cyan-400/10 text-cyan-300"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`
            }
          >
            <Settings size={18} />
            Settings
          </NavLink>
        </div>
      </aside>
    </>
  );
}
