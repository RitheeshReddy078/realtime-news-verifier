import { useState } from "react";

import {
  Search,
  ShieldCheck,
  XCircle,
  AlertTriangle,
  CircleHelp,
  LoaderCircle,
  ExternalLink,
  FileText,
  Clock3,
  Sparkles,
  RotateCcw,
} from "lucide-react";

import { verifyClaim } from "../services/api";

const verdictConfig = {
  SUPPORTED: {
    label: "Supported",
    icon: ShieldCheck,
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
    border: "border-emerald-400/20",
    description: "The available evidence supports this claim.",
  },
  CONTRADICTED: {
    label: "Contradicted",
    icon: XCircle,
    color: "text-rose-400",
    bg: "bg-rose-400/10",
    border: "border-rose-400/20",
    description: "The available evidence contradicts this claim.",
  },
  MISLEADING: {
    label: "Misleading",
    icon: AlertTriangle,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
    border: "border-amber-400/20",
    description: "The claim needs additional context.",
  },
  UNVERIFIED: {
    label: "Unverified",
    icon: CircleHelp,
    color: "text-slate-300",
    bg: "bg-slate-400/10",
    border: "border-slate-400/20",
    description:
      "There is not enough reliable evidence to verify this claim.",
  },
};

function VerdictBadge({ verdict }) {
  const config = verdictConfig[verdict] || verdictConfig.UNVERIFIED;
  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 ${config.bg} ${config.border} ${config.color}`}
    >
      <Icon size={17} />
      <span className="text-xs font-semibold sm:text-sm">
        {config.label}
      </span>
    </div>
  );
}

function EvidenceCard({ item, index, analysis }) {
  const stance = analysis?.stance || "CONTEXTUAL";

  const stanceStyles = {
    SUPPORTING:
      "border-emerald-400/20 bg-emerald-400/10 text-emerald-300",
    CONTRADICTING:
      "border-rose-400/20 bg-rose-400/10 text-rose-300",
    CONTEXTUAL:
      "border-amber-400/20 bg-amber-400/10 text-amber-300",
  };

  return (
    <article className="min-w-0 rounded-xl border border-slate-800 bg-[#0D1727] p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs font-medium text-slate-500">
          Evidence #{index + 1}
        </span>

        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
            stanceStyles[stance] || stanceStyles.CONTEXTUAL
          }`}
        >
          {stance}
        </span>
      </div>

      <p className="mt-4 break-words text-sm leading-7 text-slate-300">
        {item.evidence_sentence || "No evidence text available."}
      </p>

      {analysis?.reasoning && (
        <div className="mt-4 rounded-lg border border-slate-800 bg-[#111C2D] p-3">
          <p className="text-xs font-semibold text-slate-400">
            AI evidence analysis
          </p>

          <p className="mt-2 break-words text-xs leading-6 text-slate-400">
            {analysis.reasoning}
          </p>
        </div>
      )}

      <div className="mt-4 flex flex-col gap-3 border-t border-slate-800 pt-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <p className="break-words text-xs font-medium text-slate-300">
            {item.source_title || "Unknown source"}
          </p>

          <p className="mt-1 break-all text-xs text-slate-500">
            {item.source_domain || "Source domain unavailable"}
          </p>
        </div>

        {item.source_url && (
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex w-fit shrink-0 items-center gap-1 text-xs font-medium text-cyan-300 hover:text-cyan-200"
          >
            Open source <ExternalLink size={13} />
          </a>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
        {typeof item.similarity_score === "number" && (
          <span>
            Similarity: {(item.similarity_score * 100).toFixed(1)}%
          </span>
        )}

        {typeof item.relevance_score === "number" && (
          <span>
            Relevance: {(item.relevance_score * 100).toFixed(1)}%
          </span>
        )}
      </div>
    </article>
  );
}

export default function VerifyClaim() {
  const [claim, setClaim] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleVerify = async (event) => {
    event.preventDefault();

    if (!claim.trim()) {
      setError("Please enter a news claim before verifying.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await verifyClaim(claim.trim());

      if (!data || typeof data !== "object" || Array.isArray(data)) {
        throw new Error("The backend returned an unexpected response.");
      }

      setResult(data);
    } catch (err) {
      if (err.response) {
        setError(
          err.response.data?.detail ||
            `Backend error: ${err.response.status}`
        );
      } else if (err.code === "ECONNABORTED") {
        setError("Verification took too long. Please try again.");
      } else if (err.request) {
        setError(
          "Cannot connect to the FastAPI server. Make sure your backend is running."
        );
      } else {
        setError(err.message || "Something went wrong.");
      }
    } finally {
      setLoading(false);
    }
  };

  const resetVerification = () => {
    setResult(null);
    setError("");
    setClaim("");
  };

  const analyses = result?.evidence_analysis || [];
  const evidence = result?.evidence || [];

  const confidence =
    typeof result?.confidence_score === "number"
      ? Math.min(100, Math.max(0, result.confidence_score))
      : null;

  return (
    <div className="mx-auto min-w-0 max-w-5xl space-y-6 sm:space-y-8">

      {/* Page Heading */}
      <section className="min-w-0">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
          <Sparkles size={14} />
          AI-powered verification
        </div>

        <h1 className="text-2xl font-bold text-white sm:text-3xl">
          Verify News Claims
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-400">
          Submit a news claim and let the AI verification engine investigate
          it using live evidence and intelligent analysis.
        </p>
      </section>

      {/* Claim Input Form */}
      <form
        onSubmit={handleVerify}
        className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6"
      >
        <div className="mb-4 flex items-center gap-2">
          <Search className="shrink-0 text-cyan-300" size={20} />

          <h2 className="text-sm font-semibold text-white sm:text-base">
            Enter a claim to investigate
          </h2>
        </div>

        <textarea
          value={claim}
          onChange={(event) => setClaim(event.target.value)}
          placeholder="Example: Chandrayaan-3 successfully landed on the Moon on August 23, 2023."
          rows={5}
          maxLength={2000}
          disabled={loading}
          className="w-full min-w-0 resize-y rounded-xl border border-slate-700 bg-[#0A1423] p-3 text-sm leading-7 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/10 disabled:opacity-60 sm:p-4"
        />

        <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
          <span>Enter one clear, factual statement.</span>
          <span>{claim.length}/2000</span>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-4 break-words rounded-xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-300"
          >
            {error}
          </div>
        )}

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <button
            type="submit"
            disabled={loading || !claim.trim()}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
          >
            {loading ? (
              <>
                <LoaderCircle size={18} className="animate-spin" />
                Analyzing claim...
              </>
            ) : (
              <>
                <Search size={18} />
                Verify Claim
              </>
            )}
          </button>

          {result && (
            <button
              type="button"
              onClick={resetVerification}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 px-5 py-3 text-sm text-slate-300 transition hover:bg-slate-800 sm:w-auto"
            >
              <RotateCcw size={16} />
              New verification
            </button>
          )}
        </div>

        {loading && (
          <p className="mt-4 text-xs leading-5 text-cyan-300">
            Searching for evidence and analyzing the claim. This may take a
            little time.
          </p>
        )}
      </form>

      {/* Verification Result */}
      {result && (
        <section className="min-w-0 space-y-5 sm:space-y-6">

          {/* Result Heading */}
          <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-xl font-bold text-white">
                Verification Result
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Claim ID: {result.claim_id ?? "Unavailable"}
              </p>
            </div>

            <VerdictBadge verdict={result.verdict} />
          </div>

          {/* Confidence and Explanation */}
          <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-3">

            <div className="rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-5 md:col-span-1">
              <p className="text-sm text-slate-400">
                Confidence Score
              </p>

              <p className="mt-3 text-4xl font-bold text-cyan-300">
                {confidence !== null ? `${confidence}%` : "N/A"}
              </p>

              {confidence !== null && (
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all"
                    style={{ width: `${confidence}%` }}
                  />
                </div>
              )}
            </div>

            <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-5 md:col-span-2">
              <p className="text-sm font-semibold text-white">
                AI Explanation
              </p>

              <p className="mt-3 break-words text-sm leading-7 text-slate-400">
                {result.explanation || "No explanation was returned."}
              </p>
            </div>
          </div>

          {/* Evidence Statistics */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4">
            {[
              {
                label: "Total Evidence",
                value: result.evidence_count ?? evidence.length,
                color: "text-cyan-300",
              },
              {
                label: "Supporting",
                value: result.supporting_evidence_count ?? 0,
                color: "text-emerald-300",
              },
              {
                label: "Contradicting",
                value: result.contradicting_evidence_count ?? 0,
                color: "text-rose-300",
              },
              {
                label: "Contextual",
                value: result.contextual_evidence_count ?? 0,
                color: "text-amber-300",
              },
            ].map((item) => (
              <div
                key={item.label}
                className="min-w-0 rounded-xl border border-slate-800 bg-[#111C2D] p-4 sm:p-5"
              >
                <p className="break-words text-xs text-slate-500">
                  {item.label}
                </p>

                <p className={`mt-2 text-2xl font-bold ${item.color}`}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>

          {/* Evidence Analysis */}
          <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6">
            <div className="flex items-center gap-2">
              <FileText className="shrink-0 text-cyan-300" size={20} />

              <h3 className="font-semibold text-white">
                Evidence Analysis
              </h3>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className="max-w-full break-words rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                Status: {result.evidence_status || "Unavailable"}
              </span>

              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                {evidence.length} evidence items
              </span>
            </div>

            {evidence.length > 0 ? (
              <div className="mt-5 space-y-4">
                {evidence.map((item, index) => {
                  const analysis = analyses.find(
                    (entry) => entry.evidence_index === index + 1
                  );

                  return (
                    <EvidenceCard
                      key={`${item.source_url || "source"}-${index}`}
                      item={item}
                      index={index}
                      analysis={analysis}
                    />
                  );
                })}
              </div>
            ) : (
              <p className="mt-5 rounded-xl bg-[#0D1727] p-4 text-sm text-slate-400 sm:p-5">
                No evidence items were returned for this claim.
              </p>
            )}
          </div>

          {/* Referenced Sources */}
          {result.sources?.length > 0 && (
            <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6">
              <div className="flex items-center gap-2">
                <ExternalLink className="shrink-0 text-cyan-300" size={19} />

                <h3 className="font-semibold text-white">
                  Referenced Sources ({result.sources.length})
                </h3>
              </div>

              <div className="mt-5 grid min-w-0 gap-3 md:grid-cols-2">
                {result.sources.map((source, index) => (
                  <a
                    key={`${source.url || "source"}-${index}`}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group min-w-0 rounded-xl border border-slate-800 bg-[#0D1727] p-4 transition hover:border-cyan-400/30"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="min-w-0 break-words text-sm font-medium leading-6 text-slate-200 group-hover:text-cyan-300">
                        {source.title || "Untitled source"}
                      </p>

                      <ExternalLink
                        size={15}
                        className="mt-1 shrink-0 text-slate-500"
                      />
                    </div>

                    <p className="mt-2 break-all text-xs text-slate-500">
                      {source.domain || "Unknown domain"}
                    </p>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Related Past Events */}
          {result.past_events?.length > 0 && (
            <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6">
              <div className="flex items-center gap-2">
                <Clock3 size={19} className="shrink-0 text-cyan-300" />

                <h3 className="font-semibold text-white">
                  Related Past Events
                </h3>
              </div>

              <div className="mt-5 space-y-4">
                {result.past_events.map((event, index) => (
                  <div
                    key={`${event.event}-${index}`}
                    className="min-w-0 border-l-2 border-cyan-400/40 pl-4"
                  >
                    <p className="break-words text-sm text-slate-200">
                      {event.event}
                    </p>

                    <p className="mt-1 break-words text-xs text-slate-500">
                      {event.date} · {event.relative_time}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Current and Future Updates */}
          {result.current_and_future_updates?.length > 0 && (
            <div className="min-w-0 rounded-2xl border border-slate-800 bg-[#111C2D] p-4 sm:p-6">
              <h3 className="font-semibold text-white">
                Current and Future Updates
              </h3>

              <div className="mt-4 space-y-3">
                {result.current_and_future_updates.map((update, index) => (
                  <pre
                    key={index}
                    className="overflow-x-auto whitespace-pre-wrap break-words rounded-lg bg-[#0D1727] p-3 text-xs leading-6 text-slate-300 sm:p-4"
                  >
                    {typeof update === "string"
                      ? update
                      : JSON.stringify(update, null, 2)}
                  </pre>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Action */}
          {result.recommended_action && (
            <div className="min-w-0 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-4 sm:p-5">
              <p className="text-sm font-semibold text-cyan-300">
                Recommended Action
              </p>

              <p className="mt-2 break-words text-sm leading-6 text-slate-300">
                {typeof result.recommended_action === "string"
                  ? result.recommended_action
                  : JSON.stringify(result.recommended_action)}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
