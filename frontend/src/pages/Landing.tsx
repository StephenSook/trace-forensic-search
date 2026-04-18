import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

// ── Knowledge graph data (from graphify extraction) ──────────────────────────
interface GraphNode {
  id: string;
  label: string;
  community: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

const RAW_NODES = [
  // Frontend / UI (community 5)
  { id: "react_ui",      label: "React\nFrontend",        community: 5 },
  { id: "search_panel",  label: "Search\nPanel",          community: 5 },
  { id: "results_panel", label: "Results\nPanel",         community: 5 },
  { id: "case_detail",   label: "Case\nDetail",           community: 5 },
  // Backend / API (community 1)
  { id: "fastapi",       label: "FastAPI",                community: 1 },
  { id: "search_ep",     label: "POST\n/search",          community: 1 },
  { id: "image_ep",      label: "POST\n/search/image",    community: 1 },
  { id: "docker",        label: "Docker",                 community: 1 },
  // Database layer (community 0)
  { id: "actian",        label: "Actian\nVectorAI DB",    community: 0 },
  { id: "grpc",          label: "gRPC\nTransport",        community: 0 },
  { id: "collection",    label: "Cases\nCollection",      community: 0 },
  // Named vectors (community 4)
  { id: "phys_vec",      label: "physical_text",          community: 4 },
  { id: "circ_vec",      label: "circumstances",          community: 4 },
  { id: "cloth_vec",     label: "clothing",               community: 4 },
  { id: "image_vec",     label: "physical_image",         community: 4 },
  // Embedding models (community 3)
  { id: "bge",           label: "BGE-M3",                 community: 3 },
  { id: "sapbert",       label: "SapBERT",                community: 3 },
  { id: "clip",          label: "CLIP\nViT-B/32",         community: 3 },
  { id: "dense",         label: "Dense\nEmbed",           community: 3 },
  // Query pipeline (community 2)
  { id: "pipeline",      label: "Query\nPipeline",        community: 2 },
  { id: "hard_filter",   label: "Hard\nFilter",           community: 2 },
  { id: "multi_ret",     label: "Multi-Vector\nRetrieve", community: 2 },
  { id: "rrf",           label: "RRF\nFusion k=60",       community: 2 },
  { id: "ranked_out",    label: "Ranked\nOutput",         community: 2 },
];

const EDGES: [string, string][] = [
  // UI wiring
  ["react_ui", "search_panel"], ["react_ui", "results_panel"], ["react_ui", "case_detail"],
  ["react_ui", "search_ep"], ["react_ui", "image_ep"],
  // Backend
  ["docker", "fastapi"], ["fastapi", "search_ep"], ["fastapi", "image_ep"],
  ["fastapi", "grpc"],
  // DB layer
  ["grpc", "actian"], ["actian", "collection"],
  ["collection", "phys_vec"], ["collection", "circ_vec"],
  ["collection", "cloth_vec"], ["collection", "image_vec"],
  // Embeddings → vectors
  ["sapbert", "phys_vec"], ["bge", "circ_vec"], ["bge", "cloth_vec"], ["clip", "image_vec"],
  ["bge", "dense"],
  // Pipeline flow
  ["search_ep", "pipeline"], ["image_ep", "pipeline"],
  ["pipeline", "hard_filter"], ["hard_filter", "multi_ret"],
  ["multi_ret", "rrf"], ["rrf", "ranked_out"], ["ranked_out", "results_panel"],
  // Pipeline touches DB
  ["multi_ret", "actian"],
];

const COMMUNITY_COLORS: Record<number, string> = {
  0: "hsl(200,60%,55%)",   // DB layer — teal
  1: "hsl(211,70%,60%)",   // Backend — blue
  2: "hsl(180,55%,50%)",   // Pipeline — cyan
  3: "hsl(270,55%,65%)",   // Embeddings — purple
  4: "hsl(30,75%,57%)",    // Named vectors — orange
  5: "hsl(150,50%,52%)",   // Frontend — green
};

const GOD_NODES = new Set(["fastapi", "actian", "pipeline", "bge", "collection"]);

const COMMUNITY_LABELS: Record<number, string> = {
  0: "Database Layer",
  1: "Backend / API",
  2: "Query Pipeline",
  3: "Embedding Models",
  4: "Named Vectors",
  5: "Frontend / UI",
};

const NODE_DESC: Record<string, string> = {
  react_ui:      "Vite + React 18 · TypeScript · Tailwind · React Query for async state",
  search_panel:  "Query input, filter controls (sex, age, state, date), image upload",
  results_panel: "Ranked result cards with per-dimension scores and why-matched panel",
  case_detail:   "Full case view — all vector scores, semantic bridge table, NamUs link",
  fastapi:       "Python FastAPI · async endpoints · Pydantic validation · uvicorn server",
  search_ep:     "POST /search — text query → embed → filter → retrieve → RRF → rank",
  image_ep:      "POST /search/image · multipart upload → CLIP encode → physical_image search",
  docker:        "Actian VectorAI DB runs in Docker · offline after model download · local-first",
  actian:        "Actian VectorAI DB · named vector spaces · native filter DSL · gRPC",
  grpc:          "gRPC transport between FastAPI and Actian · low-latency binary protocol",
  collection:    "cases collection · 60 synthetic records · four named vector dimensions",
  phys_vec:      "physical_text · SapBERT 768-dim · scars, tattoos, anatomical features",
  circ_vec:      "circumstances · BGE-M3 1024-dim · disappearance narrative & location",
  cloth_vec:     "clothing · BGE-M3 1024-dim · apparel, jewelry, personal effects",
  image_vec:     "physical_image · CLIP 512-dim · tattoo photos · cross-modal text ↔ image",
  bge:           "BGE-M3 by BAAI · dense embeddings · 1024-dim · multilingual",
  sapbert:       "SapBERT by Cambridge · self-aligned on 4M+ UMLS concepts · 768-dim",
  clip:          "CLIP ViT-B/32 by OpenAI · text and image in same embedding space · 512-dim",
  dense:         "Dense vector output from BGE-M3 · semantic similarity · cosine distance",
  pipeline:      "4-stage: hard filter → multi-vector retrieve → RRF fuse → ranked output",
  hard_filter:   "Sex, age range, state, date window — eliminates impossible matches first",
  multi_ret:     "Each named vector space searched independently · results collected per dim",
  rrf:           "Reciprocal Rank Fusion k=60 · merges 4 ranked lists · no tuning required",
  ranked_out:    "Top-k results with confidence score, per-dim breakdown, semantic bridge",
};

// ── Terminology translation table ────────────────────────────────────────────
const TRANSLATIONS = [
  { fam: "Eagle tattoo, right forearm",   for_: "Avian motif dermagraphic, right ventral antebrachium" },
  { fam: "Bruise",                        for_: "Contusion / Hemorrhage / Petechiae" },
  { fam: "Birthmark on left shoulder",   for_: "Pigmented lesion, left dorsal region" },
  { fam: "He had bad teeth",             for_: "Multiple carious lesions, #14 and #19 absent" },
  { fam: "Small scar on forehead",       for_: "Linear scar, 2cm, right supraorbital region" },
  { fam: "About 5'10\"",                 for_: "Estimated stature 170–180cm, femoral length" },
  { fam: "Near a highway",               for_: "Adjacent to interstate corridor, right-of-way" },
  { fam: "Cross necklace",               for_: "Religious jewelry, cruciform pendant" },
];

// ── Pipeline steps ───────────────────────────────────────────────────────────
const PIPELINE_STEPS = [
  { num: "01", name: "Hard Filter", desc: "Sex, age range, geography, and date window eliminate impossible matches before any vector computation. Fast. Cheap. Accurate." },
  { num: "02", name: "Named Vector Search", desc: "BGE-M3 dense embeddings. physical_text, circumstances, clothing, physical_image each searched independently." },
  { num: "03", name: "RRF Fusion (k=60)", desc: "Reciprocal Rank Fusion merges four ranked result lists. Parameter-free. Consistently outperforms linear weighting." },
  { num: "04", name: "Ranked + Explained", desc: "Top candidates with per-dimension score breakdown, semantic bridge panel, and direct NamUs case link." },
];

const VECTOR_DIMS = [
  { tag: "physical_text",     model: "SapBERT · 768-dim",          items: ["Anatomical features", "Scars & marks", "Tattoo descriptions", "Dental records"] },
  { tag: "circumstances",    model: "BGE-M3 · 1024-dim",          items: ["Disappearance narrative", "Recovery environment", "Location context", "Last known activity"] },
  { tag: "clothing",         model: "BGE-M3 · 1024-dim",          items: ["Apparel description", "Personal effects", "Jewelry & accessories", "Brand / color"] },
  { tag: "physical_image",   model: "CLIP ViT-B/32 · 512-dim",    items: ["Tattoo photo upload", "Cross-modal: text ↔ image", "~80ms CPU inference", "Upload or describe"] },
];

const COMP_ROWS = [
  { name: "NamUs (NIJ)",              type: "Federal DB, keyword",    gap: "Boolean/exact match only. Free-text semantically unsearchable." },
  { name: "NCIC (FBI)",               type: "Law enforcement only",   gap: "Restricted to LE. No natural language input. No unidentified cross-match." },
  { name: "CODIS (FBI)",              type: "DNA-only",               gap: "Requires biological sample. Cannot use physical description text." },
  { name: "IdentIA (Mexico, 2026)",   type: "Tattoo image vector",    gap: "Images only. Internal forensic tool. Validates approach; leaves problem unsolved." },
  { name: "The Doe Network",          type: "Volunteer org",          gap: "Human-powered visual matching. No automation." },
  { name: "NamUs-Matching (GitHub)",  type: "LLM batch pipeline",     gap: "No front-end. No family interface. Batch-only." },
];

const STACK_ITEMS = [
  { role: "Vector Database",   name: "Actian VectorAI DB",  note: "Named vectors, filtered search, gRPC transport — the only architecture that makes this work" },
  { role: "Primary Embedding", name: "BGE-M3",              note: "Dense embeddings in one forward pass. 1024-dim. Multilingual. Handles both circumstances and clothing." },
  { role: "Clinical NLP",      name: "SapBERT",             note: "Self-aligned on 4M+ UMLS medical concepts. Maps 'bruise' and 'contusion' to the same region." },
  { role: "Multimodal",        name: "CLIP ViT-B/32",       note: "Cross-modal: upload a tattoo photo or type a description — both search the same image collection." },
  { role: "Fusion Algorithm",  name: "RRF (k=60)",          note: "Reciprocal Rank Fusion. Parameter-free. Robust. No tuning required." },
  { role: "Deployment",        name: "Docker · Offline",    note: "Fully local. Actian DB in Docker, FastAPI + models run natively. No internet after setup." },
];

// ── Knowledge Graph Canvas Component ────────────────────────────────────────
function GraphCanvas() {
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const nodesRef     = useRef<GraphNode[]>([]);
  const rafRef       = useRef<number>(0);
  const hoveredIdRef = useRef<string | null>(null);
  const [tooltip, setTooltip] = useState<{ mx: number; my: number; node: GraphNode } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let W = 0, H = 0;

    const initNodes = () => {
      nodesRef.current = RAW_NODES.map((n, i) => {
        const angle = (i / RAW_NODES.length) * Math.PI * 2;
        const r = 0.15 + Math.random() * 0.28;
        return {
          ...n,
          x: W * 0.5 + Math.cos(angle) * W * r,
          y: H * 0.5 + Math.sin(angle) * H * r,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          radius: GOD_NODES.has(n.id) ? 8 : 5.5,
        };
      });
    };

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      W = canvas.offsetWidth;
      H = canvas.offsetHeight;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      ctx.scale(dpr, dpr);
      initNodes();
    };

    const tick = () => {
      const ns = nodesRef.current;
      // Node–node repulsion
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const dx = ns[j].x - ns[i].x;
          const dy = ns[j].y - ns[i].y;
          const d  = Math.sqrt(dx * dx + dy * dy) || 1;
          const f  = 1600 / (d * d);
          ns[i].vx -= (dx / d) * f; ns[i].vy -= (dy / d) * f;
          ns[j].vx += (dx / d) * f; ns[j].vy += (dy / d) * f;
        }
      }
      // Edge spring attraction
      const nodeMap = new Map(ns.map(n => [n.id, n]));
      for (const [a, b] of EDGES) {
        const src = nodeMap.get(a), tgt = nodeMap.get(b);
        if (!src || !tgt) continue;
        const dx = tgt.x - src.x, dy = tgt.y - src.y;
        const d  = Math.sqrt(dx * dx + dy * dy) || 1;
        const f  = (d - 120) * 0.013;
        const fx = (dx / d) * f, fy = (dy / d) * f;
        src.vx += fx; src.vy += fy;
        tgt.vx -= fx; tgt.vy -= fy;
      }
      // Center gravity
      for (const n of ns) {
        n.vx += (W * 0.5 - n.x) * 0.0012;
        n.vy += (H * 0.5 - n.y) * 0.0012;
      }
      // Integrate
      const pad = 56;
      for (const n of ns) {
        n.vx *= 0.87; n.vy *= 0.87;
        n.x  += n.vx;  n.y  += n.vy;
        if (n.x < pad)     { n.x = pad;     n.vx *= -0.3; }
        if (n.x > W - pad) { n.x = W - pad; n.vx *= -0.3; }
        if (n.y < pad)     { n.y = pad;     n.vy *= -0.3; }
        if (n.y > H - pad) { n.y = H - pad; n.vy *= -0.3; }
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      const ns = nodesRef.current;
      const nodeMap = new Map(ns.map(n => [n.id, n]));

      // Edges
      for (const [a, b] of EDGES) {
        const src = nodeMap.get(a), tgt = nodeMap.get(b);
        if (!src || !tgt) continue;
        const d = Math.sqrt((tgt.x - src.x) ** 2 + (tgt.y - src.y) ** 2);
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = `hsla(211,60%,65%,${Math.max(0.04, Math.min(0.2, 160 / d))})`;
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }

      // Nodes
      for (const n of ns) {
        const color = COMMUNITY_COLORS[n.community] ?? COMMUNITY_COLORS[0];
        // Glow
        if (GOD_NODES.has(n.id)) {
          const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.radius * 3.5);
          g.addColorStop(0, color.replace("hsl(", "hsla(").replace(")", ",0.15)"));
          g.addColorStop(1, "transparent");
          ctx.beginPath(); ctx.arc(n.x, n.y, n.radius * 3.5, 0, Math.PI * 2);
          ctx.fillStyle = g; ctx.fill();
        }
        // Circle
        const isHovered = hoveredIdRef.current === n.id;
        const r = isHovered ? n.radius * 1.5 : n.radius;
        ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color.replace("hsl(", "hsla(").replace(")", isHovered ? ",1)" : ",0.8)");
        ctx.fill();
        ctx.strokeStyle = isHovered ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.12)";
        ctx.lineWidth = isHovered ? 1.5 : 0.5; ctx.stroke();
        // Label
        ctx.font = `500 8.5px 'JetBrains Mono', monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillStyle = "rgba(175,195,220,0.65)";
        const lines = n.label.split("\n");
        const lh = 10;
        const startY = n.y + n.radius + 6 + (lines.length * lh) / 2 - lh / 2;
        lines.forEach((line, i) => ctx.fillText(line, n.x, startY + (i - (lines.length - 1) / 2) * lh));
      }
    };

    const loop = () => { tick(); draw(); rafRef.current = requestAnimationFrame(loop); };

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      let nearest: GraphNode | null = null;
      let nearestD = Infinity;
      for (const n of nodesRef.current) {
        const d = Math.sqrt((n.x - mx) ** 2 + (n.y - my) ** 2);
        if (d < n.radius + 28 && d < nearestD) { nearest = n; nearestD = d; }
      }
      const newId = nearest?.id ?? null;
      if (newId !== hoveredIdRef.current) {
        hoveredIdRef.current = newId;
        setTooltip(nearest ? { mx: e.clientX, my: e.clientY, node: nearest } : null);
      }
    };

    const onMouseLeave = () => {
      hoveredIdRef.current = null;
      setTooltip(null);
    };

    // Attach to the section so events bubble up from all children (text, buttons, etc.)
    const section = canvas.closest("section") as HTMLElement | null;
    const eventTarget = section ?? canvas;

    resize();
    window.addEventListener("resize", resize);
    eventTarget.addEventListener("mousemove", onMouseMove);
    eventTarget.addEventListener("mouseleave", onMouseLeave);
    loop();

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
      eventTarget.removeEventListener("mousemove", onMouseMove);
      eventTarget.removeEventListener("mouseleave", onMouseLeave);
    };
  }, []);

  return (
    <>
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ opacity: 0.32 }}
      />
      {tooltip && (
        <div
          className="fixed z-[9999] pointer-events-none"
          style={{ left: tooltip.mx + 16, top: tooltip.my - 8 }}
        >
          <div className="bg-card border border-border rounded px-3 py-2.5 shadow-xl max-w-[240px]">
            <div className="font-mono text-[10px] tracking-[0.12em] uppercase text-primary mb-1">
              {COMMUNITY_LABELS[tooltip.node.community]}
            </div>
            <div className="font-semibold text-[13px] text-foreground mb-1 leading-snug">
              {tooltip.node.label.replace("\n", " ")}
            </div>
            <div className="font-mono text-[10px] text-muted-foreground leading-relaxed">
              {NODE_DESC[tooltip.node.id] ?? ""}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Main Landing Component ───────────────────────────────────────────────────
export default function Landing() {
  const navigate = useNavigate();
  const [exiting, setExiting] = useState(false);

  const goToSearch = useCallback(() => {
    setExiting(true);
    setTimeout(() => navigate("/search"), 420);
  }, [navigate]);

  const scrollTo = useCallback((id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  }, []);

  return (
    <div className="bg-background text-foreground font-sans overflow-x-hidden">

      {/* ── Page exit overlay ── */}
      <div
        className="fixed inset-0 z-[999] bg-background pointer-events-none"
        style={{ opacity: exiting ? 1 : 0, transition: "opacity 400ms ease" }}
      />

      {/* ── NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 h-[52px] border-b border-border bg-background/90 backdrop-blur-md">
        <span className="font-mono text-sm font-semibold tracking-[0.18em] text-foreground">
          TRACE <span className="text-muted-foreground font-normal">// FORENSIC_LEDGER</span>
        </span>
        <div className="flex items-center gap-6">
          <a href="#gap"         onClick={scrollTo("gap")}         className="font-mono text-[10px] tracking-[0.12em] uppercase text-muted-foreground hover:text-foreground transition-colors">Problem</a>
          <a href="#how"         onClick={scrollTo("how")}         className="font-mono text-[10px] tracking-[0.12em] uppercase text-muted-foreground hover:text-foreground transition-colors">Architecture</a>
          <a href="#competitive" onClick={scrollTo("competitive")} className="font-mono text-[10px] tracking-[0.12em] uppercase text-muted-foreground hover:text-foreground transition-colors">Research</a>
          <button
            onClick={goToSearch}
            className="font-mono text-[10px] tracking-[0.1em] uppercase font-semibold px-4 py-1.5 bg-primary text-primary-foreground rounded hover:opacity-90 transition-opacity"
          >
            Open Search
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-[52px]">
        <GraphCanvas />
        {/* Vignette */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 70% 70% at 50% 50%, transparent 35%, hsl(216,28%,7%) 100%)" }} />

        <div className="container mx-auto px-8 relative z-10 py-20">
          <p className="font-mono text-[10px] tracking-[0.22em] uppercase text-primary mb-6 flex items-center gap-3 animate-[fadeUp_0.6s_0.2s_both]">
            <span className="block w-8 h-px bg-primary" />
            Actian VectorAI DB Build Challenge · April 2026
          </p>

          <h1 className="text-[clamp(52px,8vw,108px)] font-light leading-[0.92] tracking-tight mb-7 animate-[fadeUp_0.7s_0.35s_both]">
            <strong className="font-semibold">Every minute,</strong>
            <br />
            someone{" "}
            <span className="text-primary">disappears.</span>
          </h1>

          <p className="text-base font-light text-muted-foreground max-w-[500px] leading-relaxed mb-12 animate-[fadeUp_0.7s_0.5s_both]">
            600,000 missing. 40,000 unidentified remains. The records that could reunite them already exist — but they speak different languages. Trace builds the semantic bridge.
          </p>

          {/* Stat strip */}
          <div className="flex w-fit border border-border bg-card mb-10 animate-[fadeUp_0.7s_0.65s_both]">
            {[
              { val: "600k",  lbl: "Missing / Year",      red: true  },
              { val: "40k",   lbl: "Unidentified Remains", red: true  },
              { val: "$1.5B", lbl: "Annual Cost",          red: true  },
              { val: "0",     lbl: "Semantic Search Tools", red: false },
            ].map((s, i) => (
              <div key={i} className="px-7 py-4 border-r border-border last:border-r-0">
                <span className={`font-mono text-[28px] font-semibold leading-none block ${s.red ? "text-destructive" : "text-primary"}`}>{s.val}</span>
                <span className="font-mono text-[9px] tracking-[0.15em] uppercase text-muted-foreground/60 mt-1 block">{s.lbl}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3 animate-[fadeUp_0.7s_0.8s_both]">
            <button
              onClick={goToSearch}
              className="font-mono text-[11px] tracking-[0.12em] uppercase font-semibold px-6 py-3 bg-primary text-primary-foreground rounded hover:opacity-90 transition-all hover:-translate-y-px flex items-center gap-2"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
              Open Search
            </button>
            <a
              href="#gap"
              onClick={scrollTo("gap")}
              className="font-mono text-[11px] tracking-[0.12em] uppercase px-5 py-3 border border-border text-muted-foreground rounded hover:border-muted-foreground hover:text-foreground transition-colors"
            >
              The Problem
            </a>
          </div>
        </div>

        {/* Graph legend */}
        <div className="absolute bottom-8 right-8 z-10">
          <p className="font-mono text-[9px] tracking-[0.15em] uppercase text-muted-foreground/50 mb-2">System Architecture Graph</p>
          <div className="flex flex-col gap-1.5">
            {[
              { color: "hsl(150,50%,52%)", label: "Frontend / UI" },
              { color: "hsl(211,70%,60%)", label: "Backend / API" },
              { color: "hsl(200,60%,55%)", label: "Database Layer" },
              { color: "hsl(180,55%,50%)", label: "Query Pipeline" },
              { color: "hsl(270,55%,65%)", label: "Embedding Models" },
              { color: "hsl(30,75%,57%)",  label: "Named Vectors" },
            ].map((l, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="w-[7px] h-[7px] rounded-full flex-shrink-0" style={{ background: l.color }} />
                <span className="font-mono text-[9px] text-muted-foreground/50">{l.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LANGUAGE GAP ── */}
      <section id="gap" className="py-[88px] border-t border-border">
        <div className="container mx-auto px-8">
          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Section 02 — The Language Gap</p>
          <h2 className="text-[clamp(28px,4vw,46px)] font-light leading-tight tracking-tight mb-4">
            Two languages.<br /><strong className="font-semibold">One person.</strong>
          </h2>
          <p className="text-[15px] text-muted-foreground leading-relaxed max-w-[600px] mb-10">
            Families describe their loved ones the way humans do — emotionally, in plain language. Medical examiners document in clinical forensic pathology: Greek roots, anatomical codes, court-admissible precision. NamUs relies on keyword search. These two records will never meet.
          </p>

          {/* Paradox callout */}
          <div className="border-l-2 border-destructive bg-destructive/5 px-6 py-5 mb-12 max-w-2xl">
            <p className="text-base italic text-foreground leading-relaxed">
              "The data required to reunite families and close these cases already exists. The problem is not a lack of records. The problem is that the records cannot find each other."
            </p>
          </div>

          {/* Translation table */}
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2.5 px-5 text-left font-mono text-[9px] tracking-[0.18em] uppercase text-muted-foreground font-medium">Family / Layperson Language</th>
                <th className="w-8" />
                <th className="py-2.5 px-5 text-left font-mono text-[9px] tracking-[0.18em] uppercase text-primary font-medium">Medical Examiner / Forensic Record</th>
              </tr>
            </thead>
            <tbody>
              {TRANSLATIONS.map((row, i) => (
                <tr key={i} className="border-b border-border/50 hover:bg-card transition-colors">
                  <td className="py-3.5 px-5 italic text-muted-foreground text-sm">{row.fam}</td>
                  <td className="text-center text-muted-foreground/50 text-xs">→</td>
                  <td className="py-3.5 px-5 font-mono text-[11px] text-primary">{row.for_}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how" className="py-[88px] border-t border-border">
        <div className="container mx-auto px-8">
          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Section 05 — Architecture</p>
          <h2 className="text-[clamp(28px,4vw,46px)] font-light leading-tight tracking-tight mb-4">
            Four stages.<br /><strong className="font-semibold">One pipeline.</strong>
          </h2>
          <p className="text-[15px] text-muted-foreground leading-relaxed max-w-[600px] mb-12">
            Hard filter → multi-vector retrieval → hybrid RRF fusion → ranked output. Every component is load-bearing.
          </p>

          <div className="grid grid-cols-4 gap-px bg-border border border-border mb-16">
            {PIPELINE_STEPS.map((s) => (
              <div key={s.num} className="bg-background p-6">
                <div className="font-mono text-[10px] tracking-[0.1em] text-muted-foreground/50 mb-3">{s.num}</div>
                <div className="text-[15px] font-medium text-foreground mb-2">{s.name}</div>
                <p className="text-[13px] text-muted-foreground leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>

          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Named Vector Architecture</p>
          <h3 className="text-[clamp(22px,3vw,34px)] font-light leading-tight tracking-tight mb-8">
            Four independent<br /><strong className="font-semibold">vector dimensions.</strong>
          </h3>
          <div className="grid grid-cols-4 gap-px bg-border border border-border">
            {VECTOR_DIMS.map((v) => (
              <div key={v.tag} className="bg-background p-[22px]">
                <span className="font-mono text-[9px] tracking-[0.12em] uppercase text-primary px-2 py-1 border border-primary/30 inline-block mb-3">{v.tag}</span>
                <div className="font-mono text-[12px] text-foreground mb-2">{v.model}</div>
                <ul className="space-y-1">
                  {v.items.map((item) => (
                    <li key={item} className="text-[12px] text-muted-foreground flex items-center gap-1.5">
                      <span className="text-primary text-[14px] leading-none">·</span>{item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LAUNCH CTA ── */}
      <section id="search-cta" className="py-[88px] border-t border-border bg-card">
        <div className="container mx-auto px-8">
          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Section 10 — Try It</p>
          <h2 className="text-[clamp(28px,4vw,46px)] font-light leading-tight tracking-tight mb-4">
            Type what you know.<br /><strong className="font-semibold">Trace finds who matches.</strong>
          </h2>
          <p className="text-[15px] text-muted-foreground leading-relaxed max-w-[580px] mb-10">
            Describe a missing person in plain language — the same way a family member would write a report. Trace translates, searches across four semantic dimensions, and shows you exactly why the match surfaced.
          </p>

          {/* Preview + CTA */}
          <div className="flex border border-border overflow-hidden">
            {/* Faux app preview */}
            <div className="flex-1 bg-background relative overflow-hidden">
              {/* Window chrome */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-card border-b border-border">
                <div className="w-2 h-2 rounded-full bg-red-400/80" />
                <div className="w-2 h-2 rounded-full bg-amber-400/80" />
                <div className="w-2 h-2 rounded-full bg-green-400/80" />
                <span className="font-mono text-[10px] text-muted-foreground/50 ml-2">localhost:8080</span>
              </div>
              {/* Faux search interface */}
              <div className="flex" style={{ minHeight: 280 }}>
                <div className="w-[230px] border-r border-border p-4 bg-card flex-shrink-0">
                  <div className="font-mono text-[11px] font-semibold tracking-[0.18em] text-foreground mb-4">
                    TRACE <span className="text-muted-foreground font-normal">// FORENSIC_LEDGER</span>
                  </div>
                  <div className="font-mono text-[8px] tracking-[0.15em] uppercase text-muted-foreground/50 mb-1.5">Describe who you're looking for</div>
                  <div className="bg-input border border-border rounded p-2.5 text-[11px] italic text-muted-foreground leading-relaxed mb-2.5">
                    My brother, 34, eagle tattoo on his right forearm, last seen near a Tennessee highway…
                  </div>
                  <div className="flex gap-1.5 flex-wrap mb-3">
                    {["Male", "TN", "Age 30–40"].map(c => (
                      <span key={c} className="font-mono text-[8px] px-2 py-0.5 border border-primary/30 rounded-full text-primary">{c}</span>
                    ))}
                  </div>
                  <div className="bg-primary text-primary-foreground rounded text-center font-mono text-[9px] font-semibold tracking-[0.1em] py-2">▸ &nbsp;Search</div>
                </div>
                <div className="flex-1 p-4 flex flex-col gap-2 overflow-hidden">
                  {/* Top result */}
                  <div className="border border-primary/30 rounded overflow-hidden">
                    <div className="bg-card px-3 py-2 flex items-center justify-between border-b border-border">
                      <span className="font-mono text-[9px] text-muted-foreground/50">UP-2020-TN-0441 · Tennessee</span>
                      <span className="font-mono text-sm font-bold text-green-400">0.94</span>
                    </div>
                    <div className="p-3">
                      <div className="font-mono text-[9px] text-primary leading-relaxed mb-2">
                        Male, mid-30s. Avian motif dermagraphic, right ventral antebrachium. Stature 178cm. I-40 corridor, 2020.
                      </div>
                      <div className="space-y-0.5">
                        {[
                          ["eagle tattoo", "avian motif dermagraphic"],
                          ["right forearm", "right ventral antebrachium"],
                          ["near a highway", "I-40 corridor"],
                        ].map(([f, r]) => (
                          <div key={f} className="grid grid-cols-[1fr_16px_1fr] gap-1 text-[8.5px]">
                            <span className="italic text-muted-foreground">{f}</span>
                            <span className="text-center text-muted-foreground/40">→</span>
                            <span className="font-mono text-primary">{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  {/* Dimmer results */}
                  {[["UP-2021-TN-0182", "0.71", "amber"], ["UP-2019-TN-0098", "0.58", "dim"]].map(([id, score, col]) => (
                    <div key={id} className="border border-border rounded">
                      <div className="bg-card px-3 py-2 flex items-center justify-between">
                        <span className="font-mono text-[9px] text-muted-foreground/50">{id} · Tennessee</span>
                        <span className={`font-mono text-sm font-bold ${col === "amber" ? "text-amber-400" : "text-muted-foreground/40"}`}>{score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {/* Right fade overlay */}
              <div className="absolute inset-y-0 right-0 w-20 pointer-events-none" style={{ background: "linear-gradient(to right, transparent, hsl(216,25%,10%))" }} />
            </div>

            {/* CTA panel */}
            <div className="flex-shrink-0 w-[300px] p-10 flex flex-col justify-center gap-5 bg-card">
              <div className="flex items-center gap-2 font-mono text-[9px] tracking-[0.2em] uppercase text-primary">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                App running
              </div>
              <div className="text-xl font-medium leading-snug text-foreground">
                The search interface<br />is ready.
              </div>
              <p className="text-[13px] text-muted-foreground leading-relaxed">
                Open the live app and run the eagle tattoo query. Watch a plain-language description surface a 0.94 semantic match with zero shared vocabulary.
              </p>
              <button
                onClick={goToSearch}
                className="flex items-center gap-2.5 w-fit font-mono text-[11px] tracking-[0.12em] uppercase font-semibold px-6 py-3 bg-primary text-primary-foreground rounded hover:opacity-90 transition-all hover:-translate-y-px"
              >
                Open Trace
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
              <span className="font-mono text-[9px] tracking-[0.08em] text-muted-foreground/40">localhost:8080 · no login required</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── COMPETITIVE ── */}
      <section id="competitive" className="py-[88px] border-t border-border">
        <div className="container mx-auto px-8">
          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Section 03 — Competitive Research</p>
          <h2 className="text-[clamp(28px,4vw,46px)] font-light leading-tight tracking-tight mb-4">
            Five research rounds.<br /><strong className="font-semibold">No existing tool solves this.</strong>
          </h2>
          <table className="w-full border-collapse mt-12">
            <thead>
              <tr className="border-b border-border">
                {["Tool / System", "Type", "Gap vs Trace"].map(h => (
                  <th key={h} className="py-2.5 px-4 text-left font-mono text-[9px] tracking-[0.15em] uppercase text-muted-foreground/50 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Trace row */}
              <tr className="border-b border-border/50 bg-primary/[0.03]">
                <td className="py-3 px-4 font-semibold text-primary text-base">Trace</td>
                <td className="py-3 px-4 text-xs text-muted-foreground">Semantic vector search</td>
                <td className="py-3 px-4 text-xs text-green-400">✓ Semantic text matching · Named vectors · Hybrid fusion · Family-facing · Offline</td>
              </tr>
              {COMP_ROWS.map((r) => (
                <tr key={r.name} className="border-b border-border/30 hover:bg-card transition-colors">
                  <td className="py-3 px-4 font-medium text-[13px] text-foreground">{r.name}</td>
                  <td className="py-3 px-4 text-xs text-muted-foreground">{r.type}</td>
                  <td className="py-3 px-4 text-xs text-muted-foreground max-w-xs leading-relaxed">{r.gap}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── STACK ── */}
      <section id="stack" className="py-[88px] border-t border-border bg-card">
        <div className="container mx-auto px-8">
          <p className="font-mono text-[9px] tracking-[0.22em] uppercase text-primary mb-4">Section 06 — Technical Stack</p>
          <h2 className="text-[clamp(28px,4vw,46px)] font-light leading-tight tracking-tight mb-12">
            Every component<br /><strong className="font-semibold">necessary. None bolted on.</strong>
          </h2>
          <div className="grid grid-cols-3 gap-px bg-border border border-border">
            {STACK_ITEMS.map((s) => (
              <div key={s.role} className="bg-background p-[22px]">
                <div className="font-mono text-[9px] tracking-[0.18em] uppercase text-muted-foreground/50 mb-1.5">{s.role}</div>
                <div className="text-[18px] font-medium text-foreground mb-1.5">{s.name}</div>
                <div className="text-[12px] text-muted-foreground leading-relaxed">{s.note}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── QUOTE ── */}
      <div className="py-[88px] border-t border-border text-center">
        <div className="container mx-auto px-8">
          <p className="text-[clamp(18px,2.5vw,28px)] font-light italic text-foreground max-w-3xl mx-auto leading-snug">
            "None of these terms share a single character. Under keyword search, these records never meet. The semantic bridge that Trace builds is the only reason this match surfaces."
          </p>
          <p className="font-mono text-[9px] tracking-[0.18em] uppercase text-muted-foreground/50 mt-5">
            Trace Project Brief · Section 10 · The Demo Moment
          </p>
        </div>
      </div>

      {/* ── FOOTER ── */}
      <footer className="border-t border-border">
        <div className="container mx-auto px-8 py-8 flex items-center justify-between">
          <span className="font-mono text-[12px] tracking-[0.2em] text-foreground">
            TRACE <span className="text-muted-foreground font-normal">// FORENSIC_LEDGER</span>
          </span>
          <div className="font-mono text-[9px] tracking-[0.1em] text-muted-foreground/50 text-right leading-relaxed">
            Semantic Matching for Missing Persons and Unidentified Remains<br />
            Actian VectorAI DB Build Challenge · April 13–25, 2026<br />
            Stephen Sookra · Vinh Le
          </div>
        </div>
      </footer>

      {/* keyframes injected via style tag */}
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
