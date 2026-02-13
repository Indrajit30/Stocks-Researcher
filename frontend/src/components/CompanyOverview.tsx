import { Company, Filing, formatMoney } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Building2, Globe, Factory, DollarSign, FileText, Calendar } from "lucide-react";

interface CompanyOverviewProps {
  company: Company;
  ticker: string;
  filing: Filing;
}

export function CompanyOverview({ company, ticker, filing }: CompanyOverviewProps) {
  return (
    <Card className="animate-fade-in">
      <CardContent className="pt-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold tracking-tight">
                {company.name || ticker}
              </h2>
              <Badge variant="secondary" className="font-mono text-sm">
                {ticker}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-2">
              {company.sector && (
                <Badge variant="outline" className="gap-1">
                  <Factory className="h-3 w-3" />
                  {company.sector}
                </Badge>
              )}
              {company.industry && (
                <Badge variant="outline" className="gap-1">
                  <Building2 className="h-3 w-3" />
                  {company.industry}
                </Badge>
              )}
              {company.country && (
                <Badge variant="outline" className="gap-1">
                  <Globe className="h-3 w-3" />
                  {company.country}
                </Badge>
              )}
              {company.market_cap && (
                <Badge variant="outline" className="gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatMoney(company.market_cap)}
                </Badge>
              )}
            </div>
          </div>

          {filing && (filing.form || filing.filing_date) && (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
              <div className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{filing.form || "Filing"}</span>
              </div>
              {filing.filing_date && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  {filing.filing_date}
                </div>
              )}
              {filing.source_url && (
                <Button variant="ghost" size="sm" asChild className="h-8">
                  <a href={filing.source_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-1" />
                    SEC
                  </a>
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
