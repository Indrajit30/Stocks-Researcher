import { Button } from "@/components/ui/button";
import { getPdfDownloadUrl } from "@/lib/api";
import { Download } from "lucide-react";

interface PdfDownloadProps {
  ticker: string;
  refresh: boolean;
  reindex: boolean;
}

export function PdfDownload({ ticker, refresh, reindex }: PdfDownloadProps) {
  const downloadUrl = getPdfDownloadUrl(ticker, refresh, reindex);

  return (
    <Button
      variant="outline"
      size="lg"
      asChild
      className="gap-2"
    >
      <a href={downloadUrl} target="_blank" rel="noopener noreferrer">
        <Download className="h-4 w-4" />
        Download PDF One-Pager
      </a>
    </Button>
  );
}
