import { useEffect, useMemo, useRef } from "react";
import { Camera, Search, Loader2, X } from "lucide-react";
import type { SearchFormState } from "@/pages/Index";

const US_STATES = [
  ["AL", "Alabama"], ["AK", "Alaska"], ["AZ", "Arizona"], ["AR", "Arkansas"],
  ["CA", "California"], ["CO", "Colorado"], ["CT", "Connecticut"], ["DE", "Delaware"],
  ["FL", "Florida"], ["GA", "Georgia"], ["HI", "Hawaii"], ["ID", "Idaho"],
  ["IL", "Illinois"], ["IN", "Indiana"], ["IA", "Iowa"], ["KS", "Kansas"],
  ["KY", "Kentucky"], ["LA", "Louisiana"], ["ME", "Maine"], ["MD", "Maryland"],
  ["MA", "Massachusetts"], ["MI", "Michigan"], ["MN", "Minnesota"], ["MS", "Mississippi"],
  ["MO", "Missouri"], ["MT", "Montana"], ["NE", "Nebraska"], ["NV", "Nevada"],
  ["NH", "New Hampshire"], ["NJ", "New Jersey"], ["NM", "New Mexico"], ["NY", "New York"],
  ["NC", "North Carolina"], ["ND", "North Dakota"], ["OH", "Ohio"], ["OK", "Oklahoma"],
  ["OR", "Oregon"], ["PA", "Pennsylvania"], ["RI", "Rhode Island"], ["SC", "South Carolina"],
  ["SD", "South Dakota"], ["TN", "Tennessee"], ["TX", "Texas"], ["UT", "Utah"],
  ["VT", "Vermont"], ["VA", "Virginia"], ["WA", "Washington"], ["WV", "West Virginia"],
  ["WI", "Wisconsin"], ["WY", "Wyoming"],
] as const;

interface TraceSearchPanelProps {
  form: SearchFormState;
  onFieldChange: (field: keyof SearchFormState, value: string) => void;
  onSubmit: () => void;
  isPending: boolean;
  imageFile: File | null;
  onImageChange: (file: File | null) => void;
}

const TraceSearchPanel = ({ form, onFieldChange, onSubmit, isPending, imageFile, onImageChange }: TraceSearchPanelProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    onImageChange(file);
  };

  const previewUrl = useMemo(() => imageFile ? URL.createObjectURL(imageFile) : null, [imageFile]);
  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);

  return (
    <div className="w-[420px] shrink-0 p-6 overflow-y-auto border-r border-border">
      {/* Title */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="font-mono text-primary font-bold text-base tracking-wide">TRACE</h2>
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse-glow" />
        </div>
        <p className="text-sm text-muted-foreground">
          Semantic search for the missing and unidentified
        </p>
      </div>

      {/* Description */}
      <div className="mb-6">
        <label className="text-trace-label block mb-2">DESCRIBE WHO YOU'RE LOOKING FOR</label>
        <textarea
          value={form.query}
          onChange={(e) => onFieldChange("query", e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full h-40 bg-input border border-border rounded-md p-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-1 focus:ring-ring font-sans"
          placeholder="Describe the person in your own words — physical features, scars, tattoos, where they were last seen, clothing…"
        />
      </div>

      {/* Visual Evidence */}
      <div className="mb-6">
        <label className="text-trace-label block mb-2">VISUAL EVIDENCE (OPTIONAL)</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
        />
        {imageFile ? (
          <div className="border border-primary/50 rounded-md p-3 bg-primary/5 flex items-center gap-3">
            <img
              src={previewUrl ?? undefined}
              alt="Upload preview"
              className="w-12 h-12 rounded object-cover"
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono text-foreground truncate">{imageFile.name}</p>
              <p className="text-[0.6rem] font-mono text-primary tracking-wide uppercase">CLIP CROSS-MODAL SEARCH ACTIVE</p>
            </div>
            <button
              onClick={() => { onImageChange(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="w-full border border-dashed border-border rounded-md p-8 flex flex-col items-center justify-center gap-2 bg-input/50 hover:bg-input/80 hover:border-primary/40 transition-colors cursor-pointer"
          >
            <Camera size={24} className="text-muted-foreground" />
            <p className="text-xs text-muted-foreground text-center font-mono tracking-wide uppercase">
              CLIP IMAGE SEARCH
            </p>
            <p className="text-[0.6rem] text-muted-foreground/60 font-mono tracking-wide uppercase">
              UPLOAD TATTOO / IDENTIFYING PHOTO
            </p>
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-trace-label block mb-2">SEX</label>
          <select
            value={form.sex}
            onChange={(e) => onFieldChange("sex", e.target.value)}
            className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none"
          >
            <option value="">Any</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Unknown">Unknown</option>
          </select>
        </div>
        <div>
          <label className="text-trace-label block mb-2">STATE</label>
          <select
            value={form.state}
            onChange={(e) => onFieldChange("state", e.target.value)}
            className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none"
          >
            <option value="">Any</option>
            {US_STATES.map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Case Type */}
      <div className="mb-4">
        <label className="text-trace-label block mb-2">CASE TYPE</label>
        <select
          value={form.caseType}
          onChange={(e) => onFieldChange("caseType", e.target.value)}
          className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none"
        >
          <option value="">Any</option>
          <option value="missing">Missing Person</option>
          <option value="unidentified">Unidentified Remains</option>
        </select>
      </div>

      {/* Age Range */}
      <div className="mb-4">
        <label className="text-trace-label block mb-2">AGE RANGE</label>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={0}
            max={120}
            value={form.ageLow}
            onChange={(e) => onFieldChange("ageLow", e.target.value)}
            placeholder="Min"
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="number"
            min={0}
            max={120}
            value={form.ageHigh}
            onChange={(e) => onFieldChange("ageHigh", e.target.value)}
            placeholder="Max"
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      {/* Date Range */}
      <div className="mb-6">
        <label className="text-trace-label block mb-2">DATE RANGE</label>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={form.dateFrom}
            onChange={(e) => onFieldChange("dateFrom", e.target.value)}
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="date"
            value={form.dateTo}
            onChange={(e) => onFieldChange("dateTo", e.target.value)}
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      {/* Execute Button */}
      <button
        onClick={onSubmit}
        disabled={isPending}
        className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded-md py-3 font-mono text-sm font-semibold tracking-wider uppercase hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isPending ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            SEARCHING...
          </>
        ) : (
          <>
            <Search size={16} />
            EXECUTE SEMANTIC QUERY
          </>
        )}
      </button>

      {/* Disclaimer */}
      <div className="mt-4 border border-primary/30 rounded-md p-3 bg-primary/5">
        <p className="text-[0.65rem] text-primary/70 font-mono leading-relaxed tracking-wide uppercase">
          DISCLAIMER: TRACE USES HIGH-CONFIDENCE SEMANTIC MATCHING MODELS. ALL RESULTS ARE PRELIMINARY AND REQUIRE VERIFICATION BY A QUALIFIED FORENSIC INVESTIGATOR.
        </p>
      </div>
    </div>
  );
};

export default TraceSearchPanel;
