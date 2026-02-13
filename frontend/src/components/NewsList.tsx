import { News, NewsArticle } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Newspaper, ExternalLink, Calendar, Globe } from "lucide-react";

interface NewsListProps {
  news: News | null | undefined;
}

function NewsItem({ article, index }: { article: NewsArticle; index: number }) {
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-3 rounded-lg hover:bg-muted/50 transition-colors group animate-slide-in"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm leading-tight group-hover:text-accent transition-colors line-clamp-2">
            {article.title}
          </h4>
          <div className="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
            {article.publishedDate && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {article.publishedDate}
              </span>
            )}
            {article.site && (
              <span className="flex items-center gap-1">
                <Globe className="h-3 w-3" />
                {article.site}
              </span>
            )}
          </div>
        </div>
        <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-accent flex-shrink-0 mt-0.5" />
      </div>
    </a>
  );
}

export function NewsList({ news }: NewsListProps) {
  const articles = news?.articles || [];
  const windowDays = news?.window_days || 7;

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Newspaper className="h-5 w-5 text-accent" />
            Latest News
          </CardTitle>
          <Badge variant="secondary" className="text-xs">
            {windowDays}D
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {articles.length > 0 ? (
          <div className="space-y-1 -mx-3">
            {articles.map((article, idx) => (
              <NewsItem key={idx} article={article} index={idx} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No news found</p>
        )}
      </CardContent>
    </Card>
  );
}
