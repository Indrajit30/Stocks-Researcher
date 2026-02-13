import { useState } from "react";
import { HeaderControls } from "@/components/HeaderControls";
import { CompanyOverview } from "@/components/CompanyOverview";
import { MetricCards } from "@/components/MetricCards";
import { OnePageSummary } from "@/components/OnePageSummary";
import { RagSectionPanel } from "@/components/RagSectionPanel";
import { BusinessSection } from "@/components/BusinessSection";
import { SwotGrid } from "@/components/SwotGrid";
import { NewsList } from "@/components/NewsList";
import { ReliabilityPanel } from "@/components/ReliabilityPanel";
import { ReportSkeleton } from "@/components/ReportSkeleton";
import { PdfDownload } from "@/components/PdfDownload";
import { fetchEquityReport, EquityReport } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { FileText } from "lucide-react";

const Index = () => {
  const [report, setReport] = useState<EquityReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastGenerated, setLastGenerated] = useState<string | undefined>();
  const [queryParams, setQueryParams] = useState({ ticker: "", refresh: false, reindex: false });
  const { toast } = useToast();

  const handleGenerate = async (ticker: string, refresh: boolean, reindex: boolean) => {
    setIsLoading(true);
    setQueryParams({ ticker, refresh, reindex });

    try {
      const data = await fetchEquityReport(ticker, refresh, reindex);
      setReport(data);
      setLastGenerated(new Date().toLocaleTimeString());

      // Show warning if there are non-fatal errors
      if (data._errors && data._errors.length > 0) {
        toast({
          title: "Report generated with warnings",
          description: `${data._errors.length} non-fatal error(s) occurred. Check the Reliability panel for details.`,
          variant: "default",
        });
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
      toast({
        title: "Failed to generate report",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <HeaderControls
        onGenerate={handleGenerate}
        isLoading={isLoading}
        lastGenerated={lastGenerated}
      />

      <main className="container px-4 py-6 md:px-6 md:py-8">
        {/* Empty State */}
        {!report && !isLoading && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <div className="h-16 w-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-6">
              <FileText className="h-8 w-8 text-accent" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight mb-2">
              Stock Fundamentals Researcher
            </h2>
            <p className="text-muted-foreground max-w-md mb-6">
              Enter a US stock ticker above to generate a comprehensive
              analyst-style report with key metrics, executive summary, SWOT
              analysis, and more.
            </p>
            <div className="flex flex-wrap gap-2 justify-center text-sm text-muted-foreground">
              <span className="px-3 py-1 rounded-full bg-muted">MSFT</span>
              <span className="px-3 py-1 rounded-full bg-muted">AAPL</span>
              <span className="px-3 py-1 rounded-full bg-muted">GOOGL</span>
              <span className="px-3 py-1 rounded-full bg-muted">AMZN</span>
              <span className="px-3 py-1 rounded-full bg-muted">NVDA</span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
              Generating report for {queryParams.ticker}... This may take a
              moment.
            </div>
            <ReportSkeleton />
          </div>
        )}

        {/* Report Content */}
        {report && !isLoading && (
          <div className="space-y-6">
            {/* Company Overview */}
            <CompanyOverview
              company={report.company}
              ticker={report.ticker}
              filing={report.filing}
            />

            {/* Key Metrics */}
            <MetricCards metrics={report.metrics} />

            {/* Executive Summary */}
            <OnePageSummary summary={report.one_page_summary} />

            {/* RAG Sections */}
            <RagSectionPanel
              sections={report.sections}
              sectionQuality={report.section_quality}
              ticker={report.ticker}
              filing={report.filing}
            />

            {/* Business Understanding */}
            <BusinessSection business={report.business} />

            {/* SWOT Analysis */}
            <SwotGrid swot={report.swot} />

            {/* News */}
            <NewsList news={report.news} />

            {/* Reliability Panel */}
            <ReliabilityPanel
              timings={report._timings_ms}
              errors={report._errors}
            />

            {/* PDF Download */}
            <div className="flex justify-center pt-4 pb-8">
              <PdfDownload
                ticker={queryParams.ticker}
                refresh={queryParams.refresh}
                reindex={queryParams.reindex}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;
