import { Bell, HelpCircle, User } from "lucide-react";

const TraceHeader = () => {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-background">
      <h2 className="font-mono text-sm tracking-[0.2em] text-foreground">
        TRACE &nbsp;// &nbsp;FORENSIC_LEDGER
      </h2>
      <div className="flex items-center gap-4">
        <button className="text-muted-foreground hover:text-foreground transition-colors">
          <Bell size={18} />
        </button>
        <button className="text-muted-foreground hover:text-foreground transition-colors">
          <HelpCircle size={18} />
        </button>
        <button className="text-muted-foreground hover:text-foreground transition-colors">
          <User size={18} />
        </button>
      </div>
    </header>
  );
};

export default TraceHeader;
