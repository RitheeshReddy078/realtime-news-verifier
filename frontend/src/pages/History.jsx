import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  Search,
  History as HistoryIcon,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  RefreshCw,
  Clock,
  FileText,
} from "lucide-react";

import { getHistory } from "../services/api";

const verdictStyles = {
  SUPPORTED: {
    label: "Supported",
    className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    icon: CheckCircle2,
  },
  CONTRADICTED: {
    label: "Contradicted",
    className: "bg-red-500/10 text-red-400 border-red-500/20",
    icon: XCircle,
  },
  MISLEADING: {
    label: "Misleading",
    className: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    icon: AlertTriangle,
  },
  UNVERIFIED: {
    label: "Unverified",
    className: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    icon: HelpCircle,
  },
};

function formatDate(dateString) {
  if (!dateString) return "Date unavailable";

  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function History() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [records, setRecords] = useState([]);

  const [search, setSearch] = useState(
    () => searchParams.get("search") || ""
  );

  const [filter, setFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch all verification records.
  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getHistory();

      setRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("History API error:", err);

      setError(
        "Unable to load verification history. Please check your backend connection."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Read search queries passed from the global Topbar.
  useEffect(() => {
    setSearch(searchParams.get("search") || "");
  }, [searchParams]);

  // Filter records using claim text, claim ID and verdict.
  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();

    return records.filter((record) => {
      const claim = String(record.claim || "").toLowerCase();
      const claimId = String(record.claim_id || "").toLowerCase();

      const matchesSearch =
        !query ||
        claim.includes(query) ||
        claimId.includes(query);

      const matchesFilter =
        filter === "ALL" || record.verdict === filter;

      return matchesSearch && matchesFilter;
    });
  }, [records, search, filter]);

  // Calculate statistics from all records.
  const counts = useMemo(() => {
    return {
      total: records.length,
      supported: records.filter(
        (r) => r.verdict === "SUPPORTED"
      ).length,
      contradicted: records.filter(
        (r) => r.verdict === "CONTRADICTED"
      ).length,
      unverified: records.filter(
        (r) => r.verdict === "UNVERIFIED"
      ).length,
      misleading: records.filter(
        (r) => r.verdict === "MISLEADING"
      ).length,
    };
  }, [records]);

  // Update URL when the History search field changes.
  const handleSearchChange = (value) => {
    setSearch(value);

    const nextParams = new URLSearchParams(searchParams);

    if (value.trim()) {
      nextParams.set("search", value);
    } else {
      nextParams.delete("search");
    }

    setSearchParams(nextParams, { replace: true });
  };

  const statistics = [
    { label: "Total", value: counts.total, color: "text-cyan-400" },
    { label: "Supported", value: counts.supported, color: "text-emerald-400" },
    { label: "Contradicted", value: counts.contradicted, color: "text-red-400" },
    { label: "Misleading", value: counts.misleading, color: "text-amber-400" },
    { label: "Unverified", value: counts.unverified, color: "text-slate-400" },
  ];

  return (
    <div className="min-h-screen bg-[#080f1c] text-white p-5 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 mb-3">
              <HistoryIcon size={18} />
              <span className="text-sm font-medium">
                Verification Records
              </span>
            </div>

            <h1 className="text-3xl font-bold">History</h1>

            <p className="text-slate-400 mt-2">
              View and manage your previously verified news claims.
            </p>
          </div>

          <button
            onClick={fetchHistory}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl
            border border-slate-700 bg-[#111d30] hover:bg-[#19283e]
            transition disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={loading ? "animate-spin" : ""}
            />
            Refresh
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {statistics.map((item) => (
            <div
              key={item.label}
              className="bg-[#111d30] border border-slate-800 rounded-2xl p-5"
            >
              <p className="text-sm text-slate-400">
                {item.label}
              </p>

              <p className={`text-3xl font-bold mt-2 ${item.color}`}>
                {item.value}
              </p>
            </div>
          ))}
        </div>

        {/* Search and filter */}
        <div className="bg-[#111d30] border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search
              size={19}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
            />

            <input
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Search by claim text or claim ID..."
              aria-label="Search verification history"
              className="w-full bg-[#0a1424] border border-slate-700 rounded-xl
              py-3 pl-12 pr-4 outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Filter by verdict"
            className="bg-[#0a1424] border border-slate-700 rounded-xl
            px-4 py-3 outline-none focus:border-cyan-500"
          >
            <option value="ALL">All verdicts</option>
            <option value="SUPPORTED">Supported</option>
            <option value="CONTRADICTED">Contradicted</option>
            <option value="MISLEADING">Misleading</option>
            <option value="UNVERIFIED">Unverified</option>
          </select>
        </div>

        {/* History records */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              Previous Verifications
            </h2>

            <span className="text-sm text-slate-400">
              {filteredRecords.length} of {records.length} records
            </span>
          </div>

          {loading ? (
            <div className="text-center py-16 text-slate-400">
              <RefreshCw
                className="animate-spin mx-auto mb-3"
                size={28}
              />
              Loading verification history...
            </div>
          ) : error ? (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-5 text-red-300">
              {error}

              <button
                onClick={fetchHistory}
                className="block mt-3 text-sm underline"
              >
                Try again
              </button>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="bg-[#111d30] border border-slate-800 rounded-2xl p-12 text-center">
              <FileText
                className="mx-auto text-slate-500 mb-4"
                size={36}
              />

              <h3 className="text-lg font-semibold">
                No records found
              </h3>

              <p className="text-slate-400 mt-2">
                Try another search or verify a new claim.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRecords.map((record) => {
                const verdict =
                  verdictStyles[record.verdict] ||
                  verdictStyles.UNVERIFIED;

                const VerdictIcon = verdict.icon;

                const sources = Array.isArray(record.sources)
                  ? record.sources
                  : [];

                const confidence = Math.min(
                  100,
                  Math.max(
                    0,
                    Number(record.confidence_score) || 0
                  )
                );

                return (
                  <div
                    key={record.claim_id}
                    className="bg-[#111d30] border border-slate-800 rounded-2xl p-5
                    hover:border-slate-600 transition"
                  >
                    {/* Claim information */}
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
                          <span>Claim #{record.claim_id}</span>
                          <span>•</span>
                          <Clock size={13} />
                          <span>
                            {formatDate(record.created_at)}
                          </span>
                        </div>

                        <h3 className="font-semibold text-lg leading-relaxed">
                          {record.claim}
                        </h3>
                      </div>

                      <span
                        className={`flex items-center gap-2 px-3 py-2 rounded-full
                        border text-xs font-semibold whitespace-nowrap ${verdict.className}`}
                      >
                        <VerdictIcon size={15} />
                        {verdict.label}
                      </span>
                    </div>

                    {/* Confidence score */}
                    <div className="mt-5">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-slate-400">
                          Confidence Score
                        </span>

                        <span className="font-semibold text-cyan-400">
                          {confidence}%
                        </span>
                      </div>

                      <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                          style={{ width: `${confidence}%` }}
                        />
                      </div>
                    </div>

                    {/* AI Explanation */}
                    <div className="mt-5 bg-[#0a1424] rounded-xl p-4">
                      <p className="text-sm font-semibold mb-2">
                        AI Explanation
                      </p>

                      <p className="text-sm text-slate-400 leading-relaxed">
                        {record.explanation ||
                          "No explanation available."}
                      </p>
                    </div>

                    {/* Sources */}
                    <div className="mt-4">
                      <p className="text-sm font-semibold mb-3">
                        Sources ({sources.length})
                      </p>

                      {sources.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {sources.map((source, index) => (
                            <a
                              key={`${record.claim_id}-${index}`}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 text-xs
                              text-cyan-400 bg-cyan-500/5 border border-cyan-500/20
                              rounded-lg px-3 py-2 hover:bg-cyan-500/10 transition"
                            >
                              <span className="max-w-[220px] truncate">
                                {source.title || "Open source"}
                              </span>

                              <ExternalLink size={13} />
                            </a>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-slate-500">
                          No sources were retrieved for this verification.
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default History;
