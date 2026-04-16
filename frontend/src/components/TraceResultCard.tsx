import { useState } from "react";
import { ChevronRight, ChevronDown, ExternalLink } from "lucide-react";
import type { ConfidenceLabel, MatchMapping } from "@/lib/api";

interface TraceResultCardProps {
  caseId: string;
  title: string;
  confidence: number;
  threshold: ConfidenceLabel | string;
  stateFound: string;
  genderEst: string;
  ageRange: string;
  discoveryDate: string;
  namusLink?: string | null;
  matchMappings: MatchMapping[];
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.85) return "bg-trace-confidence-high";
  if (confidence >= 0.6) return "bg-trace-confidence-med";
  return "bg-trace-confidence-low";
};

const TraceResultCard = ({
  caseId,
  title,
  confidence,
  threshold,
  stateFound,
  genderEst,
  ageRange,
  discoveryDate,
  namusLink,
  matchMappings,
}: TraceResultCardProps) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-border rounded-md bg-card overflow-hidden">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-3">
            <span className="text-trace-label">CASE ID: {caseId}</span>
            {namusLink && (
              <a href={namusLink} target="_blank" rel="noopener noreferrer" className="text-trace-label flex items-center gap-1 hover:text-primary transition-colors">
                NAMUS_LINK <ExternalLink size={10} />
              </a>
            )}
          </div>
          <div className="text-right">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold text-primary-foreground ${getConfidenceColor(confidence)}`}>
              CONFIDENCE {confidence.toFixed(2)}
            </span>
            <p className="text-[0.6rem] text-muted-foreground font-mono mt-1 tracking-wide uppercase">
              {threshold}
            </p>
          </div>
        </div>
        <h3 className="text-foreground font-medium text-base mb-4">{title}</h3>

        {/* Metadata grid */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          {[
            { label: "STATE_FOUND", value: stateFound },
            { label: "GENDER_EST", value: genderEst },
            { label: "AGE_RANGE", value: ageRange },
            { label: "DISCOVERY_DATE", value: discoveryDate },
          ].map((item) => (
            <div key={item.label}>
              <span className="text-trace-label block mb-1">{item.label}</span>
              <span className="text-foreground text-sm font-medium">{item.value}</span>
            </div>
          ))}
        </div>

        {/* Why This Matched toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-trace-label hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <span className="font-mono text-xs tracking-wider uppercase">WHY THIS MATCHED</span>
        </button>

        {/* Expanded match panel */}
        {expanded && (
          <div className="mt-4 border border-border rounded-md overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-muted">
                  <th className="text-left px-3 py-2 text-trace-label font-normal">QUERY_TERM</th>
                  <th className="text-left px-3 py-2 text-trace-label font-normal">FORENSIC_FIELD</th>
                  <th className="text-left px-3 py-2 text-trace-label font-normal">MATCHED_VALUE</th>
                  <th className="text-right px-3 py-2 text-trace-label font-normal">SIMILARITY</th>
                </tr>
              </thead>
              <tbody>
                {matchMappings.map((m, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="px-3 py-2.5 text-primary font-mono">{m.queryTerm}</td>
                    <td className="px-3 py-2.5 text-muted-foreground font-mono">{m.forensicField}</td>
                    <td className="px-3 py-2.5 text-foreground">{m.forensicValue}</td>
                    <td className="px-3 py-2.5 text-right font-mono text-foreground">{(m.similarity * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-end p-4 pt-0">
        <button className="border border-border rounded-md px-4 py-2 text-xs font-mono tracking-wider uppercase text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors">
          VIEW FULL CASE FILE
        </button>
      </div>
    </div>
  );
};

export default TraceResultCard;
