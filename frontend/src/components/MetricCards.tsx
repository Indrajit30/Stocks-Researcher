import { Metrics, formatPercent, formatNumber } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Percent, Scale } from "lucide-react";

interface MetricCardsProps {
  metrics: Metrics;
}

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  delay?: number;
}

function MetricCard({ label, value, icon, delay = 0 }: MetricCardProps) {
  return (
    <Card 
      className="metric-card animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
          </div>
          <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function MetricCards({ metrics }: MetricCardsProps) {
  const cagrLabel = metrics.revenue_cagr_years 
    ? `Revenue CAGR (${metrics.revenue_cagr_years}Y)` 
    : "Revenue CAGR";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <MetricCard
        label={cagrLabel}
        value={formatPercent(metrics.revenue_cagr)}
        icon={<TrendingUp className="h-5 w-5 text-accent" />}
        delay={0}
      />
      <MetricCard
        label="Operating Margin"
        value={formatPercent(metrics.operating_margin)}
        icon={<Percent className="h-5 w-5 text-accent" />}
        delay={50}
      />
      <MetricCard
        label="Net Debt / EBITDA"
        value={formatNumber(metrics.net_debt_to_ebitda)}
        icon={<Scale className="h-5 w-5 text-accent" />}
        delay={100}
      />
    </div>
  );
}
