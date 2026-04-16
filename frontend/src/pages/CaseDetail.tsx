import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, MapPin, Calendar, User, Ruler } from "lucide-react";
import TraceSidebar from "@/components/TraceSidebar";
import TraceHeader from "@/components/TraceHeader";
import { getCase, type CasePayload } from "@/lib/api";

interface LocationState {
  caseData?: CasePayload;
}

const Field = ({ label, value }: { label: string; value: string | number | null }) => (
  <div>
    <span className="text-trace-label block mb-1">{label}</span>
    <span className="text-foreground text-sm font-medium">{value ?? "—"}</span>
  </div>
);

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="border border-border rounded-md bg-card p-5">
    <span className="text-trace-header block mb-4">{title}</span>
    {children}
  </div>
);

const CaseDetail = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | null;

  const { data, isLoading, error } = useQuery({
    queryKey: ["case", caseId],
    queryFn: ({ signal }) => getCase(caseId!, signal),
    enabled: !!caseId && !state?.caseData,
  });

  const caseData: CasePayload | undefined = state?.caseData ?? data?.case;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <TraceSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TraceHeader />
        <div className="flex-1 overflow-y-auto p-6">
          {/* Back button */}
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-trace-label hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft size={14} />
            <span className="font-mono text-xs tracking-wider uppercase">BACK_TO_RESULTS</span>
          </button>

          {/* Loading */}
          {isLoading && !caseData && (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-trace-label text-xs">LOADING CASE FILE...</span>
            </div>
          )}

          {/* Error */}
          {error && !caseData && (
            <div className="border border-destructive/50 rounded-md p-4 bg-destructive/5">
              <span className="text-trace-label text-xs text-destructive block mb-1">RETRIEVAL_ERROR</span>
              <p className="text-sm text-destructive/90">{error.message}</p>
            </div>
          )}

          {/* Case content */}
          {caseData && (
            <div className="max-w-4xl space-y-6">
              {/* Case header */}
              <div className="border border-border rounded-md bg-card p-5">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <span className="text-trace-label block mb-1">CASE_FILE</span>
                    <h2 className="text-2xl font-mono font-bold text-foreground">{caseData.case_id}</h2>
                  </div>
                  <span className={`inline-flex items-center px-3 py-1.5 rounded text-xs font-mono font-bold text-primary-foreground ${
                    caseData.case_type === "missing" ? "bg-blue-600" : "bg-amber-600"
                  }`}>
                    {caseData.case_type === "missing" ? "MISSING PERSON" : "UNIDENTIFIED REMAINS"}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex items-start gap-2">
                    <MapPin size={14} className="text-muted-foreground mt-0.5 shrink-0" />
                    <Field label="STATE" value={caseData.state} />
                  </div>
                  <div className="flex items-start gap-2">
                    <User size={14} className="text-muted-foreground mt-0.5 shrink-0" />
                    <Field label="SEX" value={caseData.sex} />
                  </div>
                  <div className="flex items-start gap-2">
                    <Ruler size={14} className="text-muted-foreground mt-0.5 shrink-0" />
                    <Field label="AGE_RANGE" value={`${caseData.age_low}–${caseData.age_high} years`} />
                  </div>
                  <div className="flex items-start gap-2">
                    <Calendar size={14} className="text-muted-foreground mt-0.5 shrink-0" />
                    <Field label="DATE" value={caseData.date_iso} />
                  </div>
                </div>
              </div>

              {/* Physical description */}
              <Section title="PHYSICAL_DESCRIPTION">
                <p className="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
                  {caseData.physical_text}
                </p>
              </Section>

              {/* Circumstances */}
              <Section title="CIRCUMSTANCES">
                <p className="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
                  {caseData.circumstances}
                </p>
              </Section>

              {/* Clothing */}
              <Section title="CLOTHING_AND_EFFECTS">
                <p className="text-foreground text-sm leading-relaxed whitespace-pre-wrap">
                  {caseData.clothing}
                </p>
              </Section>

              {/* Image */}
              {caseData.image_url && (
                <Section title="ASSOCIATED_IMAGE">
                  <a
                    href={caseData.image_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary text-sm font-mono flex items-center gap-1 hover:underline"
                  >
                    {caseData.image_url} <ExternalLink size={12} />
                  </a>
                </Section>
              )}

              {/* Stream footer */}
              <div className="flex items-center gap-3 pt-4">
                <div className="flex-1 border-t border-border" />
                <span className="text-trace-label text-[0.6rem]">END OF CASE FILE</span>
                <div className="flex-1 border-t border-border" />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CaseDetail;
