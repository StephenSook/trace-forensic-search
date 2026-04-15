import TraceSidebar from "@/components/TraceSidebar";
import TraceHeader from "@/components/TraceHeader";
import TraceSearchPanel from "@/components/TraceSearchPanel";
import TraceResultsPanel from "@/components/TraceResultsPanel";

const Index = () => {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <TraceSidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TraceHeader />
        <div className="flex flex-1 overflow-hidden">
          <TraceSearchPanel />
          <TraceResultsPanel />
        </div>
      </div>
    </div>
  );
};

export default Index;
