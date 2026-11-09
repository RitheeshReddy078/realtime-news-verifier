import {
  Settings,
  ShieldCheck,
  Server,
  BrainCircuit,
  Database,
  Info,
  Code2,
} from "lucide-react";

export default function SettingsPage() {
  const settings = [
    {
      title: "Backend API",
      description: "FastAPI server connection",
      value: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
      icon: Server,
    },
    {
      title: "Database",
      description: "Verification records storage",
      value: "SQLite with SQLAlchemy",
      icon: Database,
    },
    {
      title: "AI Engine",
      description: "AI-powered claim analysis",
      value: "Google Gemini",
      icon: BrainCircuit,
    },
    {
      title: "Application",
      description: "Frontend framework",
      value: "React + Vite",
      icon: Code2,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <section>
        <div className="mb-2 flex items-center gap-2 text-cyan-300">
          <Settings size={20} />
          <span className="text-sm font-medium">
            Application Configuration
          </span>
        </div>

        <h1 className="text-3xl font-bold text-white">
          Settings
        </h1>

        <p className="mt-2 text-sm text-slate-400">
          View your TruthLens application configuration and technical
          information.
        </p>
      </section>

      {/* Application Information */}
      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300">
            <ShieldCheck size={25} />
          </div>

          <div>
            <h2 className="font-semibold text-white">
              TruthLens
            </h2>
            <p className="text-xs text-slate-500">
              Real-Time AI News Verification System
            </p>
          </div>
        </div>

        <p className="mt-5 text-sm leading-6 text-slate-400">
          TruthLens is an AI-powered news verification application
          that analyzes user-submitted claims using live web evidence,
          natural language processing and Gemini-based reasoning.
        </p>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl bg-slate-900/60 p-4">
            <p className="text-xs text-slate-500">Application Version</p>
            <p className="mt-2 font-semibold text-white">1.0.0</p>
          </div>

          <div className="rounded-xl bg-slate-900/60 p-4">
            <p className="text-xs text-slate-500">Application Status</p>
            <p className="mt-2 font-semibold text-emerald-300">
              Development
            </p>
          </div>
        </div>
      </section>

      {/* Technical Configuration */}
      <section>
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-white">
            Technical Configuration
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Technologies currently used in TruthLens.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {settings.map((item) => {
            const Icon = item.icon;

            return (
              <div
                key={item.title}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300">
                    <Icon size={20} />
                  </div>

                  <div>
                    <h3 className="font-medium text-white">
                      {item.title}
                    </h3>
                    <p className="text-xs text-slate-500">
                      {item.description}
                    </p>
                  </div>
                </div>

                <p className="mt-5 break-all text-sm font-medium text-cyan-300">
                  {item.value}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Information */}
      <section className="rounded-2xl border border-cyan-400/10 bg-cyan-400/5 p-5">
        <div className="flex items-center gap-2 text-cyan-300">
          <Info size={19} />
          <h3 className="font-semibold">About This Application</h3>
        </div>

        <p className="mt-3 text-sm leading-6 text-slate-400">
          This page currently displays application information and
          configuration. API keys and other sensitive credentials
          are intentionally not displayed in the frontend.
        </p>
      </section>
    </div>
  );
}
