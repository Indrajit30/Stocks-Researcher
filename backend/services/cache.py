import json
import time
from pathlib import Path
from datetime import date
from typing import Any, Optional

CACHE_DIR = Path("data/cache")

def _ensure_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def make_key(endpoint: str, ticker: str, asof: Optional[str] = None) -> str:
    asof = asof or date.today().isoformat()
    safe = endpoint.replace("/", "_").replace(" ", "_")
    return f"{safe}_{ticker.upper()}_{asof}.json"

def load_cache(key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
    """
    Loads cache if it exists and hasn't exceeded the ttl_seconds.
    """
    _ensure_dir()
    path = CACHE_DIR / key
    
    if not path.exists():
        return None

    # TTL Check: Compare current time to file modification time
    if ttl_seconds is not None:
        file_age = time.time() - path.stat().st_mtime
        if file_age > ttl_seconds:
            path.unlink()  # Delete expired file
            return None

    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        path.unlink()  # corrupted cache
        return None


def save_cache(key: str, obj: Any) -> None:
    _ensure_dir()
    path = CACHE_DIR / key
    path.write_text(json.dumps(obj, indent=2, default=str))

def clear_old_cache(days_to_keep: int = 7) -> None:
    """
    Deletes all cache files older than X days to save disk space.
    """
    if not CACHE_DIR.exists():
        return
    
    seconds_in_day = 86400
    cutoff = time.time() - (days_to_keep * seconds_in_day)
    
    for file in CACHE_DIR.glob("*.json"):
        if file.stat().st_mtime < cutoff:
            file.unlink()