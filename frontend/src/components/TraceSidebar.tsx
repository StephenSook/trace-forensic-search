import { LayoutDashboard, Search, Radio, FileText, Terminal, Plus, Shield, Settings } from "lucide-react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", active: true },
  { icon: Search, label: "Investigations" },
  { icon: Radio, label: "Evidence" },
  { icon: FileText, label: "Reports" },
  { icon: Terminal, label: "System Logs" },
];

const bottomItems = [
  { icon: Shield, label: "Security" },
  { icon: Settings, label: "Settings" },
];

const TraceSidebar = () => {
  return (
    <aside className="w-56 flex flex-col bg-sidebar border-r border-border shrink-0">
      {/* Brand */}
      <div className="p-5 pb-6">
        <h1 className="font-mono text-primary font-bold text-lg tracking-wide">TRACE_FS</h1>
        <span className="text-trace-label text-[0.6rem]">V_4.02_STABLE</span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 flex flex-col gap-0.5 px-3">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
              item.active
                ? "bg-sidebar-accent text-primary"
                : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }`}
          >
            <item.icon size={16} />
            <span className="font-mono text-xs tracking-wide uppercase">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* New Query Button */}
      <div className="px-3 mb-4">
        <button className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground rounded-md py-2.5 text-xs font-mono font-semibold tracking-wider uppercase hover:bg-primary/90 transition-colors">
          <Plus size={14} />
          NEW_QUERY
        </button>
      </div>

      {/* Bottom nav */}
      <div className="px-3 pb-5 flex flex-col gap-0.5">
        {bottomItems.map((item) => (
          <button
            key={item.label}
            className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
          >
            <item.icon size={16} />
            <span className="font-mono text-xs tracking-wide uppercase">{item.label}</span>
          </button>
        ))}
      </div>
    </aside>
  );
};

export default TraceSidebar;
