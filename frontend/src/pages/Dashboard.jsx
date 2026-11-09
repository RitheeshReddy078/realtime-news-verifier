import { useEffect, useMemo, useState } from "react";
import {
  ShieldCheck,
  XCircle,
  AlertTriangle,
  CircleHelp,
  ScanSearch,
  ArrowUpRight,
  Clock3,
  RefreshCw,
} from "lucide-react";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import StatCard from "../components/dashboard/StatCard";
import { getHistory } from "../services/api";

const verdictColors = {
  SUPPORTED: "#34d399",
  CONTRADICTED: "#fb7185",
  MISLEADING: "#fbbf24",
  UNVERIFIED: "#94a3b8",
};

const formatDate = (date) => {
  if (!date) return "Date unavailable";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) return "Date unavailable";

  return parsedDate.toLocaleString();
};

export default function Dashboard() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getHistory();

      const historyRecords = Array.isArray(data)
        ? data
        : data?.records ?? data?.history ?? data?.data ?? [];

      setRecords(Array.isArray(historyRecords) ? historyRecords : []);
    } catch (err) {
      console.error("Dashboard API error:", err);
      setError(
        "Unable to load dashboard data. Check your backend connection."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const counts = useMemo(() => {
    const result = {
      SUPPORTED: 0,
      CONTRADICTED: 0,
      MISLEADING: 0,
      UNVERIFIED: 0,
    };

    records.forEach((record) => {
      const verdict = String(record.verdict || "").toUpperCase();

      if (Object.prototype.hasOwnProperty.call(result, verdict)) {
        result[verdict]++;
      }
    });

    return result;
  }, [records]);

  const stats = [
    {
      title: "Total Verified",
      value: records.length,
      description: "Total claims processed",
      icon: ShieldCheck,
      color: "bg-cyan-400/10 text-cyan-300",
    },
    {
      title: "Supported",
      value: counts.SUPPORTED,
      description: "Claims supported by evidence",
      icon: ShieldCheck,
      color: "bg-emerald-400/10 text-emerald-300",
    },
    {
      title: "Contradicted",
      value: counts.CONTRADICTED,
      description: "Claims contradicted by evidence",
      icon: XCircle,
      color: "bg-rose-400/10 text-rose-300",
    },
    {
      title: "Misleading",
      value: counts.MISLEADING,
      description: "Claims containing misleading information",
      icon: AlertTriangle,
      color: "bg-amber-400/10 text-amber-300",
    },
    {
      title: "Unverified",
      value: counts.UNVERIFIED,
      description: "Claims without sufficient evidence",
      icon: CircleHelp,
      color: "bg-slate-400/10 text-slate-300",
    },
  ];

  const chartData = Object.entries(counts)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({
      name,
      value,
      color: verdictColors[name],
    }));

  const recentRecords = [...records]
    .sort(
      (a, b) =>
        new Date(b.created_at || 0) - new Date(a.created_at || 0)
    )
    .slice(0, 5);

  return (
    <div className="min-w-0 space-y-6 sm:space-y-8">

      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-cyan-400/15 bg-gradient-to-r from-cyan-950/60 via-[#11243A] to-violet-950/40 p-5 sm:p-8">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            AI-powered news intelligence
          </div>

          <h1 className="text-2xl font-bold leading-tight text-white sm:text-3xl md:text-4xl">
            Separate facts from
            <span className="text-cyan-300"> misinformation.</span>
          </h1>

          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400 sm:mt-4">
            Analyze news claims using real-time search, natural language
            processing and AI-powered evidence evaluation.
          </p>

          <a
            href="/verify"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 sm:mt-6 sm:px-5"
          >
            <ScanSearch size={18} />
            Verify a news claim
            <ArrowUpRight size={17} />
          </a>
        </div>

        <div className="pointer-events-none absolute -right-10 -top-20 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl" />
      </section>

      {/* Statistics */}
      <section>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 sm:mb-5">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Verification Overview
            </h2>

            <p className="mt-1 text-xs text-slate-500 sm:text-sm">
              Live statistics from your verification history.
            </p>
          </div>

          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-300 transition hover:bg-slate-800 disabled:opacity-50"
          >
            <RefreshCw
              size={14}
              className={loading ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-5">
          {stats.map((stat, index) => (
            <div
              key={stat.title}
              className={index === 0 ? "col-span-2 xl:col-span-1" : ""}
            >
              <StatCard
                {...stat}
                value={loading ? "—" : stat.value}
              />
            </div>
          ))}
        </div>
      </section>

      {/* Recent History and Chart */}
      <section className="grid min-w-0 grid-cols-1 gap-4 xl:grid-cols-3 xl:gap-5">

        {/* Recent Verifications */}
        <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6 xl:col-span-2">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="font-semibold text-white">
                Recent Verifications
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Your latest analyzed news claims
              </p>
            </div>

            <Clock3 className="shrink-0 text-slate-500" size={20} />
          </div>

          {loading ? (
            <div className="flex min-h-48 items-center justify-center text-sm text-slate-400">
              Loading verification history...
            </div>
          ) : recentRecords.length === 0 ? (
            <div className="flex min-h-48 flex-col items-center justify-center text-center">
              <ScanSearch size={28} className="text-slate-500" />

              <h3 className="mt-4 text-sm font-medium text-white">
                No verification records found
              </h3>

              <p className="mt-2 text-xs text-slate-500">
                Verify a news claim to see your results here.
              </p>
            </div>
          ) : (
            <div className="mt-5 space-y-3">
              {recentRecords.map((record, index) => {
                const verdict = String(
                  record.verdict || "UNVERIFIED"
                ).toUpperCase();

                const badgeColor =
                  verdict === "SUPPORTED"
                    ? "bg-emerald-400/10 text-emerald-300"
                    : verdict === "CONTRADICTED"
                    ? "bg-rose-400/10 text-rose-300"
                    : verdict === "MISLEADING"
                    ? "bg-amber-400/10 text-amber-300"
                    : "bg-slate-400/10 text-slate-300";

                return (
                  <div
                    key={record.claim_id ?? index}
                    className="min-w-0 rounded-xl border border-slate-800 bg-slate-900/40 p-3 sm:p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs text-slate-500">
                        Claim #{record.claim_id ?? "—"}
                      </span>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${badgeColor}`}
                      >
                        {verdict}
                      </span>
                    </div>

                    <p className="mt-3 break-words text-sm leading-6 text-slate-200">
                      {record.claim}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                      <span>
                        Confidence: {record.confidence_score ?? "—"}%
                      </span>

                      <span>{formatDate(record.created_at)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Verdict Distribution */}
        <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6">
          <h2 className="font-semibold text-white">
            Verdict Distribution
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Overview of claim classifications
          </p>

          {loading ? (
            <div className="flex min-h-64 items-center justify-center text-sm text-slate-400">
              Loading chart...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex min-h-64 flex-col items-center justify-center text-center">
              <AlertTriangle size={28} className="text-slate-500" />

              <p className="mt-4 text-sm text-slate-400">
                No chart data available
              </p>

              <p className="mt-2 text-xs text-slate-500">
                Verify claims to populate this chart.
              </p>
            </div>
          ) : (
            <div className="h-64 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="43%"
                    innerRadius={48}
                    outerRadius={75}
                    paddingAngle={4}
                  >
                    {chartData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: "10px",
                      color: "#fff",
                    }}
                  />

                  <Legend
                    verticalAlign="bottom"
                    iconType="circle"
                    formatter={(value) => (
                      <span className="text-xs text-slate-400">
                        {value}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
