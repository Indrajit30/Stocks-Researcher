import requests
from datetime import date, timedelta
from typing import Any, Dict, List
import os


def is_relevant_to_ticker(article: Dict[str, Any], ticker: str, company_name: str = "") -> bool:
    """
    Filter out articles that aren't actually about the company.
    """
    ticker_upper = ticker.upper()
    title = (article.get('title') or '').upper()
    text = (article.get('text') or '').upper()
    
    # Check if ticker appears with $ symbol or in parentheses
    if f"${ticker_upper}" in title or f"({ticker_upper})" in title:
        return True
    
    # Check if ticker appears as standalone word in title
    if f" {ticker_upper} " in f" {title} ":
        return True
    
    # Check if company name is in title
    if company_name and company_name.upper() in title:
        return True
    
    # Exclude obvious noise
    noise_keywords = [
        'SHOW HN:', 'ASK HN:', 'GITHUB.COM',
        'SIGN UP', 'BONUS', 'REFERRAL', 'PROMO',
        'OZBARGAIN', 'WEBULL'
    ]
    
    if any(keyword in title for keyword in noise_keywords):
        return False
    
    # If ticker or company not in title, check first part of description
    text_start = text[:300]
    if f"${ticker_upper}" in text_start or f"({ticker_upper})" in text_start:
        return True
    
    if company_name and company_name.upper() in text_start:
        return True
    
    return False


def get_stock_news(ticker: str, days: int = 7, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch stock news using NewsAPI with relevance filtering.
    
    Get your free API key from: https://newsapi.org/register
    Free tier: 100 requests/day, 1 request/second
    """
    # Get API key from environment variable
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    
    if not NEWS_API_KEY:
        print("Warning: NEWS_API_KEY not set. Please set it in your environment or .env file")
        return []
    
    to_dt = date.today()
    from_dt = to_dt - timedelta(days=days)
    
    # Map common tickers to company names for better filtering
    company_map = {
        "MSFT": "Microsoft",
        "AAPL": "Apple",
        "GOOGL": "Google",
        "GOOG": "Alphabet",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "NVDA": "Nvidia",
        "META": "Meta",
        "NFLX": "Netflix",
        # Add more as needed
    }
    
    company_name = company_map.get(ticker.upper(), "")
    
    # Construct search query
    # Using quotes and OR operators for better precision
    if company_name:
        search_query = f'("{company_name}" OR ${ticker.upper()} OR ({ticker.upper()}))'
    else:
        search_query = f'(${ticker.upper()} OR ({ticker.upper()}))'
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": search_query,
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,  # Get more to filter from
        "apiKey": NEWS_API_KEY,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return []
        
        articles = data.get("articles", [])
        
        # Filter and normalize articles
        out: List[Dict[str, Any]] = []
        for article in articles:
            normalized_article = {
                "ticker": ticker.upper(),
                "publishedDate": article.get("publishedAt"),
                "title": article.get("title"),
                "text": article.get("description"),
                "site": article.get("source", {}).get("name"),
                "url": article.get("url"),
                "image": article.get("urlToImage"),
                "symbol": ticker.upper(),
            }
            
            # Apply relevance filter
            if is_relevant_to_ticker(normalized_article, ticker, company_name):
                out.append(normalized_article)
            
            # Stop once we have enough
            if len(out) >= limit:
                break
        
        return out
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []


# Alternative: Use Finnhub (also free, no credit card required)
def get_stock_news_finnhub(ticker: str, days: int = 7, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch stock news using Finnhub API.
    
    Get your free API key from: https://finnhub.io/register
    Free tier: 60 API calls/minute
    """
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    
    if not FINNHUB_API_KEY:
        print("Warning: FINNHUB_API_KEY not set")
        return []
    
    to_dt = date.today()
    from_dt = to_dt - timedelta(days=days)
    
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker.upper(),
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
        "token": FINNHUB_API_KEY,
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            return []
        
        out: List[Dict[str, Any]] = []
        for article in data[:limit]:
            # Convert Unix timestamp to ISO format
            pub_date = None
            if article.get("datetime"):
                from datetime import datetime
                pub_date = datetime.fromtimestamp(article["datetime"]).isoformat() + "Z"
            
            out.append({
                "ticker": ticker.upper(),
                "publishedDate": pub_date,
                "title": article.get("headline"),
                "text": article.get("summary"),
                "site": article.get("source"),
                "url": article.get("url"),
                "image": article.get("image"),
                "symbol": ticker.upper(),
            })
        
        return out
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news from Finnhub: {e}")
        return []


# Fallback: Combine multiple sources
def get_stock_news_combined(ticker: str, days: int = 7, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Try multiple news sources and combine results.
    """
    all_articles = []
    
    # Try Finnhub first (more reliable for stock-specific news)
    finnhub_articles = get_stock_news_finnhub(ticker, days, limit)
    all_articles.extend(finnhub_articles)
    
    # If we don't have enough, try NewsAPI
    if len(all_articles) < limit:
        remaining = limit - len(all_articles)
        newsapi_articles = get_stock_news(ticker, days, remaining)
        all_articles.extend(newsapi_articles)
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        url = article.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
    
    # Sort by date
    unique_articles.sort(key=lambda x: x.get("publishedDate") or "", reverse=True)
    
    return unique_articles[:limit]