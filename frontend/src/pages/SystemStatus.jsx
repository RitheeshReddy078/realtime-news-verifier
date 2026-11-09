import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Server,
  Database,
  BrainCircuit,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock3,
} from "lucide-react";

import { getHealth } from "../services/api";

export default function SystemStatus() {
  const [backendStatus, setBackendStatus] = useState("checking");
  const [databaseStatus, setDatabaseStatus] = useState("checking");
  const [geminiStatus, setGeminiStatus] = useState("checking");
  const [lastChecked, setLastChecked] = useState(null);

  const checkSystem = useCallback(async () => {
    try {
      setBackendStatus("checking");
      setDatabaseStatus("checking");
      setGeminiStatus("checking");

      const response = await getHealth();

      const apiHealthy = ["healthy", "ok"].includes(
        String(response?.status || "").toLowerCase()
      );

      setBackendStatus(apiHealthy ? "online" : "offline");

      const dbHealthy =
        String(response?.database || "").toLowerCase() === "operational";

      setDatabaseStatus(
        !apiHealthy ? "unknown" : dbHealthy ? "online" : "offline"
      );

      const aiHealthy =
        String(response?.gemini || "").toLowerCase() === "operational";

      setGeminiStatus(
        !apiHealthy ? "unknown" : aiHealthy ? "online" : "offline"
      );
    } catch (error) {
      console.error("Health check failed:", error);

      setBackendStatus("offline");
      setDatabaseStatus("unknown");
      setGeminiStatus("unknown");
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    checkSystem();
  }, [checkSystem]);

  const statusStyles = {
    online: {
      label: "Operational",
      color: "text-emerald-300",
      background: "bg-emerald-400/10",
      icon: CheckCircle2,
    },
    offline: {
      label: "Unavailable",
      color: "text-rose-300",
      background: "bg-rose-400/10",
      icon: XCircle,
    },
    checking: {
      label: "Checking...",
      color: "text-amber-300",
      background: "bg-amber-400/10",
      icon: RefreshCw,
    },
    unknown: {
      label: "Not checked",
      color: "text-slate-300",
      background: "bg-slate-700/60",
      icon: Activity,
    },
  };

  const services = [
    {
      name: "FastAPI Backend",
      description: "API server and request processing",
      icon: Server,
      status: backendStatus,
      detail: "Checked through the /health endpoint",
    },
    {
      name: "Database",
      description: "Verification records and history storage",
      icon: Database,
      status: databaseStatus,
      detail: "Connection tested using SQL SELECT 1",
    },
    {
      name: "AI Verification Engine",
      description: "Gemini-powered claim analysis",
      icon: BrainCircuit,
      status: geminiStatus,
      detail: "Gemini model accessibility check",
    },
  ];

  const currentStatus = statusStyles[backendStatus];
  const StatusIcon = currentStatus.icon;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <section>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-cyan-300">
              <Activity size={20} />
              <span className="text-sm font-medium">
                System Monitoring
              </span>
            </div>

            <h1 className="text-3xl font-bold text-white">
              System Status
            </h1>

            <p className="mt-2 text-sm text-slate-400">
              Monitor the availability of your TruthLens services.
            </p>
          </div>

          <button
            onClick={checkSystem}
            disabled={backendStatus === "checking"}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={
                backendStatus === "checking" ? "animate-spin" : ""
              }
            />
            Refresh Status
          </button>
        </div>
      </section>

      {/* Overall Backend Status */}
      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl ${currentStatus.background} ${currentStatus.color}`}
            >
              <StatusIcon size={28} />
            </div>

            <div>
              <p className="text-sm text-slate-400">
                Backend API Status
              </p>
              <h2 className={`mt-1 text-xl font-bold ${currentStatus.color}`}>
                {currentStatus.label}
              </h2>
            </div>
          </div>

          <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
            GET /health
          </span>
        </div>

        <div className="mt-6 border-t border-slate-800 pt-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Clock3 size={14} />
            Last checked:{" "}
            {lastChecked ? lastChecked.toLocaleString() : "Not checked yet"}
          </div>
        </div>
      </section>

      {/* Service Components */}
      <section>
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-white">
            Service Components
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Live health-check information for your application.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {services.map((service) => {
            const Icon = service.icon;
            const serviceStatus = statusStyles[service.status];
            const ServiceStatusIcon = serviceStatus.icon;

            return (
              <div
                key={service.name}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300">
                    <Icon size={22} />
                  </div>

                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${serviceStatus.background} ${serviceStatus.color}`}
                  >
                    <ServiceStatusIcon size={13} />
                    {serviceStatus.label}
                  </span>
                </div>

                <h3 className="mt-5 font-semibold text-white">
                  {service.name}
                </h3>

                <p className="mt-2 text-sm text-slate-400">
                  {service.description}
                </p>

                <p className="mt-4 text-xs leading-5 text-slate-500">
                  {service.detail}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Information */}
      <section className="rounded-2xl border border-cyan-400/10 bg-cyan-400/5 p-5">
        <h3 className="font-semibold text-cyan-300">
          About System Monitoring
        </h3>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          TruthLens uses FastAPI for backend processing, SQLAlchemy
          for database connectivity, and Gemini for AI-powered claim
          analysis. The system checks backend availability, database
          connectivity, and Gemini model accessibility through the
          health endpoint.
        </p>
      </section>
    </div>
  );
}
