import { Search, Plus } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";

const TraceSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isSearch = location.pathname === "/";

  return (
    <aside className="w-56 flex flex-col bg-sidebar border-r border-border shrink-0">
      {/* Brand */}
      <div className="p-5 pb-6">
        <h1 className="font-mono text-primary font-bold text-lg tracking-wide">TRACE_FS</h1>
        <span className="text-trace-label text-[0.6rem]">V_4.02_STABLE</span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 flex flex-col gap-0.5 px-3">
        <button
          onClick={() => navigate("/")}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
            isSearch
              ? "bg-sidebar-accent text-primary"
              : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          }`}
        >
          <Search size={16} />
          <span className="font-mono text-xs tracking-wide uppercase">Search</span>
        </button>
      </nav>

      {/* New Query Button */}
      <div className="px-3 pb-5">
        <button
          onClick={() => navigate("/")}
          className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded-md py-2.5 text-xs font-mono font-semibold tracking-wider uppercase hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          NEW_QUERY
        </button>
      </div>
    </aside>
  );
};

export default TraceSidebar;
