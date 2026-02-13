import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, FileText, AlertCircle } from "lucide-react";
import { fetchChunk, ChunkResponse } from "@/lib/api";

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  ticker: string;
  form: string;
  filingDate: string;
  chunkId: string;
  sourceUrl?: string;
}

export function EvidenceModal({
  isOpen,
  onClose,
  ticker,
  form,
  filingDate,
  chunkId,
  sourceUrl,
}: EvidenceModalProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ChunkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadChunk = async () => {
    if (data) return; // Already loaded
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchChunk(ticker, form, filingDate, chunkId);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evidence");
    } finally {
      setLoading(false);
    }
  };

  // Load when opened
  if (isOpen && !data && !loading && !error) {
    loadChunk();
  }

  const handleClose = () => {
    setData(null);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-accent" />
            Evidence Chunk
          </DialogTitle>
          <div className="flex items-center gap-2 pt-2">
            <Badge variant="secondary" className="font-mono text-xs">
              {chunkId}
            </Badge>
            {data?.section && (
              <Badge variant="outline" className="text-xs">
                {data.section}
              </Badge>
            )}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-auto">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-accent" />
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {data && !data.found && (
            <div className="flex items-center gap-2 p-4 rounded-lg bg-warning/10 text-warning">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm">{data.message || "Chunk not found"}</p>
            </div>
          )}

          {data?.found && data.text && (
            <div className="space-y-4">
              <pre className="p-4 rounded-lg bg-muted font-mono text-xs leading-relaxed whitespace-pre-wrap overflow-auto max-h-[50vh]">
                {data.text}
              </pre>
            </div>
          )}
        </div>

        {sourceUrl && (
          <div className="pt-4 border-t">
            <Button variant="outline" size="sm" asChild>
              <a href={sourceUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                View Source on SEC
              </a>
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
