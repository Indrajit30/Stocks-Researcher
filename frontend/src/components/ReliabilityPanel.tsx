import { ApiError } from "@/lib/api";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, ChevronDown, Settings } from "lucide-react";
import { useState } from "react";

interface ReliabilityPanelProps {
  timings?: Record<string, number>;
  errors?: ApiError[];
}

export function ReliabilityPanel({ timings, errors }: ReliabilityPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const hasData = (timings && Object.keys(timings).length > 0) || (errors && errors.length > 0);

  if (!hasData) {
    return null;
  }

  // Sort timings by duration (slowest first)
  const sortedTimings = timings
    ? Object.entries(timings).sort(([, a], [, b]) => b - a)
    : [];

  return (
    <Card className="animate-fade-in">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CardHeader className="py-3">
          <CollapsibleTrigger className="flex items-center justify-between w-full hover:bg-muted/50 -mx-2 px-2 py-1 rounded transition-colors">
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              <Settings className="h-4 w-4 text-muted-foreground" />
              Reliability & Diagnostics
              {errors && errors.length > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {errors.length} warning{errors.length > 1 ? "s" : ""}
                </Badge>
              )}
            </CardTitle>
            <ChevronDown
              className={`h-4 w-4 text-muted-foreground transition-transform ${
                isOpen ? "rotate-180" : ""
              }`}
            />
          </CollapsibleTrigger>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="pt-0 space-y-4">
            {/* Errors */}
            {errors && errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Non-fatal Errors
                </h4>
                <div className="space-y-2">
                  {errors.map((error, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded bg-destructive/10 border border-destructive/20 text-xs"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {error.step}
                        </Badge>
                        <span className="font-mono text-destructive">
                          {error.error_type}
                        </span>
                      </div>
                      <p className="text-muted-foreground">{error.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timings */}
            {sortedTimings.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Execution Timings (slowest first)
                </h4>
                <div className="space-y-1">
                  {sortedTimings.map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center justify-between py-1 px-2 rounded bg-muted/50 text-xs"
                    >
                      <span className="font-mono">{key}</span>
                      <span className="text-muted-foreground">
                        {value >= 1000
                          ? `${(value / 1000).toFixed(2)}s`
                          : `${value.toFixed(0)}ms`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
