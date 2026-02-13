import { Swot, SwotSection } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Target, TrendingUp, TrendingDown, AlertTriangle, Lightbulb } from "lucide-react";

interface SwotGridProps {
  swot: Swot | null | undefined;
}

interface SwotQuadrantProps {
  title: string;
  type: "strength" | "weakness" | "opportunity" | "threat";
  icon: React.ReactNode;
  section: SwotSection | string[] | null | undefined;
}

function renderBullets(section: SwotSection | string[] | null | undefined): string[] {
  if (!section) return [];
  
  if (Array.isArray(section)) return section;
  
  if (typeof section === "object" && "bullets" in section) {
    return section.bullets || [];
  }
  
  return [];
}

function SwotQuadrant({ title, type, icon, section }: SwotQuadrantProps) {
  const bullets = renderBullets(section);
  
  const classMap = {
    strength: "swot-strength",
    weakness: "swot-weakness",
    opportunity: "swot-opportunity",
    threat: "swot-threat",
  };

  return (
    <div className={`swot-card ${classMap[type]}`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h4 className="font-semibold text-sm">{title}</h4>
      </div>
      {bullets.length > 0 ? (
        <ul className="space-y-2">
          {bullets.map((bullet, idx) => (
            <li key={idx} className="text-sm leading-relaxed flex items-start gap-2">
              <span className="w-1 h-1 rounded-full bg-current mt-2 flex-shrink-0 opacity-50" />
              {bullet}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">No data available</p>
      )}
    </div>
  );
}

export function SwotGrid({ swot }: SwotGridProps) {
  if (!swot) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-accent" />
            SWOT Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No SWOT analysis available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5 text-accent" />
          SWOT Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SwotQuadrant
            title="Strengths"
            type="strength"
            icon={<TrendingUp className="h-4 w-4 text-swot-strength" />}
            section={swot.strengths}
          />
          <SwotQuadrant
            title="Weaknesses"
            type="weakness"
            icon={<TrendingDown className="h-4 w-4 text-swot-weakness" />}
            section={swot.weaknesses}
          />
          <SwotQuadrant
            title="Opportunities"
            type="opportunity"
            icon={<Lightbulb className="h-4 w-4 text-swot-opportunity" />}
            section={swot.opportunities}
          />
          <SwotQuadrant
            title="Threats"
            type="threat"
            icon={<AlertTriangle className="h-4 w-4 text-swot-threat" />}
            section={swot.threats}
          />
        </div>
      </CardContent>
    </Card>
  );
}
