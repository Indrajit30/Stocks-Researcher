import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { FileText, RefreshCw, Database, Loader2 } from "lucide-react";

interface HeaderControlsProps {
  onGenerate: (ticker: string, refresh: boolean, reindex: boolean) => void;
  isLoading: boolean;
  lastGenerated?: string;
}

export function HeaderControls({ onGenerate, isLoading, lastGenerated }: HeaderControlsProps) {
  const [ticker, setTicker] = useState("");
  const [refresh, setRefresh] = useState(false);
  const [reindex, setReindex] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onGenerate(ticker.trim().toUpperCase(), refresh, reindex);
    }
  };

  const isValid = ticker.trim().length > 0;

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-16 items-center gap-4 px-4 md:px-6">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-accent" />
          <h1 className="text-lg font-semibold tracking-tight hidden sm:block">
            Stock Fundamentals Researcher
          </h1>
          <h1 className="text-lg font-semibold tracking-tight sm:hidden">
            Stock Intel
          </h1>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-1 items-center gap-3 md:gap-4"
        >
          <div className="relative flex-1 max-w-xs">
            <Input
              type="text"
              placeholder="Enter ticker (e.g., MSFT)"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="uppercase font-mono"
              disabled={isLoading}
            />
          </div>

          <Button
            type="submit"
            disabled={!isValid || isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="hidden sm:inline">Generating...</span>
              </>
            ) : (
              <>
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">Generate Report</span>
                <span className="sm:hidden">Go</span>
              </>
            )}
          </Button>

          <div className="hidden lg:flex items-center gap-4 ml-2 pl-4 border-l">
            <div className="flex items-center gap-2">
              <Switch
                id="refresh"
                checked={refresh}
                onCheckedChange={setRefresh}
                disabled={isLoading}
              />
              <Label
                htmlFor="refresh"
                className="text-sm text-muted-foreground flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" />
                Refresh
              </Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="reindex"
                checked={reindex}
                onCheckedChange={setReindex}
                disabled={isLoading}
              />
              <Label
                htmlFor="reindex"
                className="text-sm text-muted-foreground flex items-center gap-1"
              >
                <Database className="h-3 w-3" />
                Reindex
              </Label>
            </div>
          </div>
        </form>

        {lastGenerated && (
          <div className="hidden md:block text-xs text-muted-foreground">
            Last: {lastGenerated}
          </div>
        )}
      </div>
    </header>
  );
}
