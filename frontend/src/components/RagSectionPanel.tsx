import { useState } from "react";
import { Section, SectionQuality, Citation, Filing } from "@/lib/api";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EvidenceModal } from "./EvidenceModal";
import { FileSearch, Quote, Eye, TrendingUp, AlertTriangle, DollarSign, Layers } from "lucide-react";

interface RagSectionPanelProps {
  sections: Section[];
  sectionQuality?: Record<string, SectionQuality>;
  ticker: string;
  filing: Filing;
}

const SECTION_ICONS: Record<string, React.ReactNode> = {
  "Quarter highlights": <TrendingUp className="h-4 w-4" />,
  "Investment & CAPEX signals": <DollarSign className="h-4 w-4" />,
  "Risks mentioned in filing": <AlertTriangle className="h-4 w-4" />,
  "Segment / product drivers": <Layers className="h-4 w-4" />,
};

function CitationRow({
  citation,
  ticker,
  filing,
  index,
}: {
  citation: Citation;
  ticker: string;
  filing: Filing;
  index: number;
}) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <div className="flex items-center justify-between gap-2 py-1.5 px-2 rounded bg-muted/50 text-xs">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Quote className="h-3 w-3 text-muted-foreground flex-shrink-0" />
          <code className="font-mono truncate">{citation.chunk_id}</code>
          {citation.section && (
            <span className="text-muted-foreground truncate hidden sm:inline">
              • {citation.section}
            </span>
          )}
          {citation.score !== undefined && (
            <Badge variant="outline" className="text-xs ml-auto hidden md:inline-flex">
              {citation.score.toFixed(2)}
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={() => setShowModal(true)}
        >
          <Eye className="h-3 w-3 mr-1" />
          Show
        </Button>
      </div>

      <EvidenceModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        ticker={ticker}
        form={filing.form || "10-Q"}
        filingDate={filing.filing_date || ""}
        chunkId={citation.chunk_id}
        sourceUrl={citation.source_url}
      />
    </>
  );
}

export function RagSectionPanel({
  sections,
  sectionQuality,
  ticker,
  filing,
}: RagSectionPanelProps) {
  if (!sections || sections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5 text-accent" />
            Insights from SEC Filings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No sections available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSearch className="h-5 w-5 text-accent" />
          Insights from SEC Filings
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Accordion
          type="multiple"
          defaultValue={[sections[0]?.title]}
          className="space-y-2"
        >
          {sections.map((section, idx) => {
            const quality = sectionQuality?.[section.title];
            const icon = SECTION_ICONS[section.title] || (
              <FileSearch className="h-4 w-4" />
            );

            return (
              <AccordionItem
                key={idx}
                value={section.title}
                className="border rounded-lg px-4"
              >
                <AccordionTrigger className="hover:no-underline py-3">
                  <div className="flex items-center gap-3 text-left">
                    <span className="text-accent">{icon}</span>
                    <span className="font-medium">{section.title}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="space-y-4">
                    {/* Bullets */}
                    {section.bullets && section.bullets.length > 0 ? (
                      <div className="bullet-list">
                        {section.bullets.map((bullet, bIdx) => (
                          <div key={bIdx} className="bullet-item">
                            <div className="bullet-marker" />
                            <p
                              dangerouslySetInnerHTML={{
                                __html: bullet.replace(
                                  /\*\*(.*?)\*\*/g,
                                  "<strong>$1</strong>"
                                ),
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No data available
                      </p>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            );
          })}
        </Accordion>
      </CardContent>
    </Card>
  );
}
