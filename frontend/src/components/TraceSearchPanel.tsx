import { Camera, Search } from "lucide-react";

const TraceSearchPanel = () => {
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
          className="w-full h-40 bg-input border border-border rounded-md p-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-1 focus:ring-ring font-sans"
          placeholder="e.g. My brother, 34, eagle tattoo on his right forearm, last seen near a Tennessee highway in 2019..."
        />
      </div>

      {/* Visual Evidence */}
      <div className="mb-6">
        <label className="text-trace-label block mb-2">VISUAL EVIDENCE (OPTIONAL)</label>
        <div className="border border-dashed border-border rounded-md p-8 flex flex-col items-center justify-center gap-2 bg-input/50 cursor-pointer hover:border-muted-foreground transition-colors">
          <Camera size={24} className="text-muted-foreground" />
          <p className="text-xs text-muted-foreground text-center font-mono tracking-wide uppercase">
            UPLOAD TATTOO OR IDENTIFYING PHOTO
          </p>
          <p className="text-xs text-muted-foreground font-mono tracking-wide uppercase">
            DRAG AND DROP TO ATTACH
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-trace-label block mb-2">SEX</label>
          <select className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none">
            <option>Male</option>
            <option>Female</option>
            <option>Unknown</option>
          </select>
        </div>
        <div>
          <label className="text-trace-label block mb-2">STATE</label>
          <select className="w-full bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring appearance-none">
            <option>Tennessee</option>
            <option>Alabama</option>
            <option>Georgia</option>
            <option>Kentucky</option>
          </select>
        </div>
      </div>

      {/* Age Range */}
      <div className="mb-4">
        <label className="text-trace-label block mb-2">AGE RANGE</label>
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Min"
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="text"
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
            type="text"
            placeholder="mm/dd/yyyy"
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground">—</span>
          <input
            type="text"
            placeholder="mm/dd/yyyy"
            className="flex-1 bg-input border border-border rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      {/* Execute Button */}
      <button className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded-md py-3 font-mono text-sm font-semibold tracking-wider uppercase hover:bg-primary/90 transition-colors">
        <Search size={16} />
        EXECUTE SEMANTIC QUERY
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
