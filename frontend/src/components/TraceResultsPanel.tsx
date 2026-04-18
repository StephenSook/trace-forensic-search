import { Search } from "lucide-react";
import TraceResultCard from "./TraceResultCard";
import type { SearchResponse } from "@/lib/api";

interface TraceResultsPanelProps {
  data?: SearchResponse;
  isPending: boolean;
  error: Error | null;
}

const TraceResultsPanel = ({ data, isPending, error }: TraceResultsPanelProps) => {
  const hasSearched = data !== undefined;
  const results = hasSearched ? (data.results ?? []) : [];
  const matchCount = hasSearched ? (data.total_matches ?? results.length) : 0;

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      {/* Results Header */}
      <div className="flex items-end justify-between mb-6">
        <div>
          <span className="text-trace-header block mb-1">RESULTS_QUERY_LOG</span>
          <div className="flex items-baseline gap-3">
            <span className="text-5xl font-mono font-bold text-foreground leading-none">
              {isPending ? "—" : matchCount}
            </span>
            <span className="text-trace-header">MATCHES FOUND</span>
          </div>
        </div>
        <div>
          <span className="text-trace-label">SORT: PROBABILITY SCORE</span>
          <span className="text-muted-foreground ml-1">∨</span>
        </div>
      </div>

      {/* Loading state */}
      {isPending && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-trace-label text-xs">EXECUTING SEMANTIC QUERY...</span>
        </div>
      )}

      {/* Error state */}
      {!isPending && error && (
        <div className="mb-6 border border-destructive/50 rounded-md p-4 bg-destructive/5">
          <span className="text-trace-label text-xs text-destructive block mb-1">QUERY_ERROR</span>
          <p className="text-sm text-destructive/90">{error.message}</p>
        </div>
      )}

      {/* Empty state — before any search or after a search with no results */}
      {!isPending && !error && results.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Search size={32} className="text-muted-foreground" />
          <span className="text-trace-label text-xs">
            {hasSearched ? "NO MATCHES FOUND" : "AWAITING QUERY"}
          </span>
          <p className="text-xs text-muted-foreground max-w-xs text-center">
            {hasSearched
              ? "Try broadening your description or removing filters."
              : "Describe who you're looking for to begin semantic search."}
          </p>
        </div>
      )}


      {/* Result Cards */}
      {!isPending && results.length > 0 && (
        <div className="flex flex-col gap-4">
          {results.map((result) => (
            <TraceResultCard key={result.caseId} {...result} />
          ))}
        </div>
      )}

      {/* Stream end */}
      {!isPending && results.length > 0 && (
        <div className="mt-8 flex flex-col items-center gap-2">
          <div className="flex items-center gap-3 w-full">
            <div className="flex-1 border-t border-border" />
            <span className="text-trace-label text-[0.6rem]">END OF SEMANTIC STREAM</span>
            <div className="flex-1 border-t border-border" />
          </div>
          {data && (
            <span className="text-[0.55rem] text-muted-foreground font-mono tracking-wider">
              QUERY_LATENCY:{data.latency_ms}MS
            </span>
          )}
        </div>
      )}

    </div>
  );
};

export default TraceResultsPanel;
