import { Wifi, Search } from "lucide-react";
import TraceResultCard from "./TraceResultCard";
import type { SearchResponse } from "@/lib/api";

const mockResults = [
  {
    caseId: "UP10294",
    title: "Unidentified Male (Found 2019)",
    confidence: 0.94,
    threshold: "HIGH CONFIDENCE" as const,
    stateFound: "Tennessee",
    genderEst: "Male",
    ageRange: "30 - 45 Years",
    discoveryDate: "Oct 14, 2019",
    matchMappings: [
      { queryTerm: '"brother, 34"', forensicField: "BIOLOGICAL_RELATION / AGE_EST", forensicValue: "Male, 30–45 yrs", similarity: 0.96 },
      { queryTerm: '"eagle tattoo"', forensicField: "DISTINGUISHING_MARKS", forensicValue: "Large avian tattoo, right forearm", similarity: 0.93 },
      { queryTerm: '"right forearm"', forensicField: "MARK_LOCATION", forensicValue: "Right anterior forearm", similarity: 0.98 },
      { queryTerm: '"Tennessee highway"', forensicField: "RECOVERY_LOCATION", forensicValue: "I-40 corridor, Cocke County TN", similarity: 0.91 },
      { queryTerm: '"2019"', forensicField: "DISCOVERY_DATE", forensicValue: "2019-10-14", similarity: 0.95 },
    ],
  },
  {
    caseId: "UP9982",
    title: "Human Remains - Unspecified",
    confidence: 0.71,
    threshold: "MEDIUM CONFIDENCE" as const,
    stateFound: "Tennessee",
    genderEst: "Indeterminate",
    ageRange: "25 - 40 Years",
    discoveryDate: "Mar 02, 2020",
    matchMappings: [
      { queryTerm: '"Tennessee"', forensicField: "STATE_FOUND", forensicValue: "Tennessee", similarity: 1.0 },
      { queryTerm: '"34" (age)', forensicField: "AGE_EST", forensicValue: "25–40 yrs", similarity: 0.72 },
      { queryTerm: '"2019"', forensicField: "DISCOVERY_DATE", forensicValue: "2020-03-02", similarity: 0.61 },
    ],
  },
];

interface TraceResultsPanelProps {
  data?: SearchResponse;
  isPending: boolean;
  error: Error | null;
}

const TraceResultsPanel = ({ data, isPending, error }: TraceResultsPanelProps) => {
  const results = data?.results ?? mockResults;
  const matchCount = data?.total_matches ?? results.length;
  const hasSearched = data !== undefined;

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

      {/* Empty state after a real search */}
      {!isPending && hasSearched && !error && results.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Search size={32} className="text-muted-foreground" />
          <span className="text-trace-label text-xs">NO MATCHES FOUND</span>
          <p className="text-xs text-muted-foreground max-w-xs text-center">
            Try broadening your description or removing filters.
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
          {!data && (
            <span className="text-[0.55rem] text-muted-foreground font-mono tracking-wider">
              QUERY_COMPLETE:DEMO_PREVIEW
            </span>
          )}
        </div>
      )}

      {/* FAB */}
      <div className="fixed bottom-6 right-6">
        <button className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors">
          <Wifi size={18} />
        </button>
      </div>
    </div>
  );
};

export default TraceResultsPanel;
