import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import TraceSidebar from "@/components/TraceSidebar";
import TraceHeader from "@/components/TraceHeader";
import TraceSearchPanel from "@/components/TraceSearchPanel";
import TraceResultsPanel from "@/components/TraceResultsPanel";
import { searchCases, ApiError, type SearchRequest, type SearchResponse } from "@/lib/api";

export interface SearchFormState {
  query: string;
  sex: string;
  state: string;
  ageLow: string;
  ageHigh: string;
  dateFrom: string;
  dateTo: string;
}

const INITIAL_FORM: SearchFormState = {
  query: "",
  sex: "",
  state: "",
  ageLow: "",
  ageHigh: "",
  dateFrom: "",
  dateTo: "",
};

export function buildRequest(form: SearchFormState): SearchRequest {
  const filters: SearchRequest["filters"] = {};
  if (form.sex) filters.sex = form.sex as "Male" | "Female" | "Unknown";
  if (form.state) filters.state = form.state;

  const ageLow = parseInt(form.ageLow, 10);
  if (!Number.isNaN(ageLow)) filters.age_low = ageLow;
  const ageHigh = parseInt(form.ageHigh, 10);
  if (!Number.isNaN(ageHigh)) filters.age_high = ageHigh;

  if (form.dateFrom) filters.date_from = form.dateFrom;
  if (form.dateTo) filters.date_to = form.dateTo;

  return {
    query: form.query,
    filters: Object.keys(filters).length > 0 ? filters : undefined,
    limit: 10,
  };
}

const Index = () => {
  const [form, setForm] = useState<SearchFormState>(INITIAL_FORM);

  const handleFieldChange = (field: keyof SearchFormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const mutation = useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (req) => searchCases(req),
    onError: (err) => {
      const message =
        err instanceof ApiError
          ? `Search failed (${err.status}): ${err.message}`
          : `Network error: ${err.message}`;
      toast.error(message);
    },
  });

  const handleSubmit = () => {
    if (mutation.isPending) return;
    if (!form.query.trim()) {
      toast.error("Enter a description before searching.");
      return;
    }
    mutation.mutate(buildRequest(form));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <TraceSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TraceHeader />
        <div className="flex flex-1 overflow-hidden">
          <TraceSearchPanel
            form={form}
            onFieldChange={handleFieldChange}
            onSubmit={handleSubmit}
            isPending={mutation.isPending}
          />
          <TraceResultsPanel
            data={mutation.data}
            isPending={mutation.isPending}
            error={mutation.error}
          />
        </div>
      </div>
    </div>
  );
};

export default Index;
