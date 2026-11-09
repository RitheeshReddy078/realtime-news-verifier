import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import {
  Search,
  CircleHelp,
  X,
  ArrowUpRight,
  ShieldCheck,
  FileSearch,
  Clock,
  AlertCircle,
} from "lucide-react";

import { getHistory } from "../../services/api";

const pageDetails = {
  "/": {
    title: "Dashboard",
    section: "Workspace / Overview",
  },
  "/verify": {
    title: "Verify News",
    section: "Workspace / Verification",
  },
  "/history": {
    title: "History",
    section: "Workspace / Records",
  },
  "/status": {
    title: "System Status",
    section: "Workspace / Monitoring",
  },
  "/settings": {
    title: "Settings",
    section: "Workspace / Configuration",
  },
};

export default function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const searchRef = useRef(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [records, setRecords] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [showHelp, setShowHelp] = useState(false);

  const currentPage = pageDetails[location.pathname] || {
    title: "TruthLens",
    section: "Workspace",
  };

  useEffect(() => {
    let isMounted = true;

    const loadRecords = async () => {
      setSearchLoading(true);
      setSearchError("");

      try {
        const data = await getHistory();

        if (isMounted) {
          setRecords(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        if (isMounted) {
          setSearchError("Unable to load verification records.");
        }
      } finally {
        if (isMounted) {
          setSearchLoading(false);
        }
      }
    };

    loadRecords();

    return () => {
      isMounted = false;
    };
  }, []);

  // Keyboard shortcut: Ctrl + K / Cmd + K
  useEffect(() => {
    const handleShortcut = (event) => {
      if (
        (event.ctrlKey || event.metaKey) &&
        event.key.toLowerCase() === "k"
      ) {
        event.preventDefault();
        searchRef.current?.focus();
      }

      if (event.key === "Escape") {
        setSearchQuery("");
        searchRef.current?.blur();
        setShowHelp(false);
      }
    };

    window.addEventListener("keydown", handleShortcut);

    return () => {
      window.removeEventListener("keydown", handleShortcut);
    };
  }, []);

  const filteredRecords = searchQuery.trim()
    ? records
        .filter((record) => {
          const query = searchQuery.trim().toLowerCase();

          return (
            String(record.claim || "").toLowerCase().includes(query) ||
            String(record.claim_id || "").toLowerCase().includes(query)
          );
        })
        .slice(0, 8)
    : [];

  const openSearchResult = (record) => {
    navigate(
      `/history?search=${encodeURIComponent(record.claim || "")}`
    );

    setSearchQuery("");
    searchRef.current?.blur();
  };

  return (
    <header className="relative z-30 flex flex-col gap-3 border-b border-slate-800 bg-[#080E1A]/95 px-4 py-4 sm:px-6 md:h-20 md:flex-row md:items-center md:justify-between md:gap-4 md:px-8 md:py-0">

      {/* Page information */}
      <div className="min-w-0 pl-12 md:pl-0">
        <p className="truncate text-xs text-slate-500 sm:text-sm">
          {currentPage.section}
        </p>

        <h2 className="truncate text-lg font-semibold text-white sm:text-xl">
          {currentPage.title}
        </h2>
      </div>

      {/* Search and Help */}
      <div className="flex w-full items-center gap-3 md:w-auto md:justify-end">

        {/* Global Search */}
        <div className="relative min-w-0 flex-1 md:w-64 md:flex-none">
          <div className="flex w-full items-center gap-2 rounded-xl border border-slate-800 bg-[#111C2D] px-3 py-2.5 transition focus-within:border-cyan-400">
            <Search size={17} className="shrink-0 text-slate-500" />

            <input
              ref={searchRef}
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search claims..."
              aria-label="Search verification claims"
              className="w-full min-w-0 bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
            />

            {searchQuery ? (
              <button
                onClick={() => setSearchQuery("")}
                aria-label="Clear search"
                className="shrink-0 text-slate-400 hover:text-white"
              >
                <X size={15} />
              </button>
            ) : (
              <span className="hidden shrink-0 rounded bg-slate-800 px-2 py-1 text-xs text-slate-400 lg:block">
                Ctrl K
              </span>
            )}
          </div>

          {/* Search results */}
          {searchQuery.trim() && (
            <div className="absolute left-0 right-0 top-full mt-2 max-h-80 w-full overflow-y-auto rounded-xl border border-slate-700 bg-[#111C2D] p-2 shadow-2xl md:left-auto md:right-0 md:w-96">

              <div className="border-b border-slate-800 px-3 py-2">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                  Search Results
                </p>
              </div>

              {searchLoading ? (
                <div className="p-5 text-center text-sm text-slate-400">
                  Loading verification records...
                </div>
              ) : searchError ? (
                <div className="flex items-center gap-2 p-4 text-sm text-red-400">
                  <AlertCircle size={16} />
                  {searchError}
                </div>
              ) : filteredRecords.length > 0 ? (
                filteredRecords.map((record) => (
                  <button
                    key={record.claim_id}
                    onClick={() => openSearchResult(record)}
                    className="flex w-full items-start gap-3 rounded-lg p-3 text-left transition hover:bg-slate-800"
                  >
                    <FileSearch
                      size={17}
                      className="mt-1 shrink-0 text-cyan-400"
                    />

                    <div className="min-w-0 flex-1">
                      <p className="line-clamp-2 break-words text-sm text-slate-200">
                        {record.claim}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Claim #{record.claim_id} · {record.verdict}
                      </p>
                    </div>

                    <ArrowUpRight
                      size={15}
                      className="shrink-0 text-slate-500"
                    />
                  </button>
                ))
              ) : (
                <div className="p-5 text-center">
                  <Search
                    size={22}
                    className="mx-auto mb-2 text-slate-500"
                  />

                  <p className="text-sm text-slate-300">
                    No matching claims found.
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Try another keyword or claim ID.
                  </p>
                </div>
              )}

              {filteredRecords.length > 0 && (
                <p className="border-t border-slate-800 px-3 py-2 text-xs text-slate-500">
                  Showing up to 8 matching records
                </p>
              )}
            </div>
          )}
        </div>

        {/* Help */}
        <div className="relative shrink-0">
          <button
            onClick={() => setShowHelp(!showHelp)}
            aria-label="Help"
            aria-expanded={showHelp}
            className={`rounded-xl border p-2.5 transition ${
              showHelp
                ? "border-cyan-400 bg-cyan-400/10 text-cyan-300"
                : "border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
          >
            {showHelp ? <X size={19} /> : <CircleHelp size={19} />}
          </button>

          {showHelp && (
            <div className="fixed right-3 top-28 z-50 w-[calc(100vw-1.5rem)] max-w-80 rounded-xl border border-slate-700 bg-[#111C2D] p-4 shadow-2xl md:absolute md:right-0 md:top-full md:mt-2 md:w-80">

              <div className="mb-4 flex items-center gap-2">
                <ShieldCheck size={20} className="text-cyan-400" />

                <h3 className="font-semibold text-white">
                  TruthLens Help
                </h3>
              </div>

              <div className="space-y-4">
                <div className="flex gap-3">
                  <FileSearch
                    size={18}
                    className="shrink-0 text-cyan-400"
                  />

                  <div>
                    <p className="text-sm font-medium text-white">
                      Verify a claim
                    </p>

                    <p className="text-xs leading-5 text-slate-400">
                      Enter a factual news statement to analyze it using
                      live evidence and AI.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <ShieldCheck
                    size={18}
                    className="shrink-0 text-emerald-400"
                  />

                  <div>
                    <p className="text-sm font-medium text-white">
                      Understand verdicts
                    </p>

                    <p className="text-xs leading-5 text-slate-400">
                      Supported, Contradicted, Misleading and Unverified
                      describe the evidence assessment.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Clock
                    size={18}
                    className="shrink-0 text-cyan-400"
                  />

                  <div>
                    <p className="text-sm font-medium text-white">
                      View history
                    </p>

                    <p className="text-xs leading-5 text-slate-400">
                      Review previous claims, confidence scores,
                      explanations and sources.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={() => {
                  setShowHelp(false);
                  navigate("/verify");
                }}
                className="mt-5 w-full rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Verify a Claim
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
