import { OnePageSummary as OnePageSummaryType, Bullet } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Quote } from "lucide-react";

interface OnePageSummaryProps {
  summary: OnePageSummaryType | null | undefined;
}

function BulletItem({ bullet, index }: { bullet: Bullet; index: number }) {
  return (
    <div 
      className="flex items-start gap-3 animate-slide-in"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="bullet-marker mt-2" />
      <div className="flex-1 min-w-0">
        <p className="text-sm leading-relaxed">
          {bullet.label && (
            <span className="font-semibold text-accent mr-1">{bullet.label}</span>
          )}
          {bullet.text}
        </p>
      </div>
    </div>
  );
}

export function OnePageSummary({ summary }: OnePageSummaryProps) {
  if (!summary || !summary.bullets || summary.bullets.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-accent" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No summary available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-accent" />
          Executive Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bullet-list space-y-4">
          {summary.bullets.slice(0, 8).map((bullet, index) => (
            <BulletItem key={index} bullet={bullet} index={index} />
          ))}
        </div>
        {summary.notes && (
          <p className="mt-4 text-xs text-muted-foreground italic border-t pt-3">
            {summary.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
