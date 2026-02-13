import { Business, BusinessBlock } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building, DollarSign, Globe, BarChart3 } from "lucide-react";

interface BusinessSectionProps {
  business: Business | null | undefined;
}

interface SubSectionProps {
  title: string;
  icon: React.ReactNode;
  block: BusinessBlock | string[] | string | null | undefined;
}

function renderBullets(block: BusinessBlock | string[] | string | null | undefined): string[] {
  if (!block) return [];
  
  if (typeof block === "string") return [block];
  
  if (Array.isArray(block)) return block;
  
  if (typeof block === "object" && "bullets" in block) {
    return block.bullets || [];
  }
  
  return [];
}

function SubSection({ title, icon, block }: SubSectionProps) {
  const bullets = renderBullets(block);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-accent">{icon}</span>
        <h4 className="font-medium text-sm">{title}</h4>
      </div>
      {bullets.length > 0 ? (
        <div className="bullet-list pl-6">
          {bullets.map((bullet, idx) => (
            <div key={idx} className="bullet-item">
              <div className="bullet-marker" />
              <p className="text-sm">{bullet}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground pl-6">No data available</p>
      )}
    </div>
  );
}

export function BusinessSection({ business }: BusinessSectionProps) {
  if (!business) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5 text-accent" />
            Understanding the Business
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No business information available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building className="h-5 w-5 text-accent" />
          Understanding the Business
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SubSection
            title="Company Segments"
            icon={<Building className="h-4 w-4" />}
            block={business.segments}
          />
          <SubSection
            title="Revenue Characteristics"
            icon={<DollarSign className="h-4 w-4" />}
            block={business.revenue_characteristics}
          />
          <SubSection
            title="Geography"
            icon={<Globe className="h-4 w-4" />}
            block={business.geographies || business.geography}
          />
          <SubSection
            title="Key Performance Indicators"
            icon={<BarChart3 className="h-4 w-4" />}
            block={business.kpis}
          />
        </div>
      </CardContent>
    </Card>
  );
}
