from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import re
import time

import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/Mazennaji/internship-scraper)"
TIMEOUT_SECONDS = 8
DELAY_SECONDS = 0.6
CACHE_DIR = Path("cache")

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})

_last_request_time = 0.0

stats = {"fetches": 0, "cache_hits": 0}


@dataclass
class FetchResult:
    status: int
    html: str | None
    cached: bool
    error: str | None = None


def _cache_path_for(url: str) -> Path:
    parsed = urlparse(url)
    path = parsed.path

    page_match = re.search(r"page-(\d+)\.html$", path)
    if page_match or path in ("/index.html", "/"):
        n = page_match.group(1) if page_match else "1"
        return CACHE_DIR / f"catalogue-page-{n}.html"

    segments = [s for s in path.split("/") if s]
    name = segments[-1] if segments else "page"
    if name == "index.html" and len(segments) > 1:
        name = segments[-2]
    name = re.sub(r"\.html$", "", name)
    return CACHE_DIR / f"{name}.html"


def _throttle() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < DELAY_SECONDS:
        time.sleep(DELAY_SECONDS - elapsed)
    _last_request_time = time.monotonic()


def _polite_request(url: str, allow_retry: bool = True) -> FetchResult:
    _throttle()
    try:
        response = _session.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        if allow_retry:
            time.sleep(1)
            return _polite_request(url, allow_retry=False)
        return FetchResult(status=0, html=None, cached=False, error=str(exc))

    if 500 <= response.status_code < 600 and allow_retry:
        time.sleep(1)
        return _polite_request(url, allow_retry=False)

    if response.status_code == 200 and "charset" not in response.headers.get("Content-Type", "").lower():
        response.encoding = response.apparent_encoding

    html = response.text if response.status_code == 200 else None
    return FetchResult(status=response.status_code, html=html, cached=False)


def fetch_and_cache(url: str) -> FetchResult:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path_for(url)

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")
        stats["cache_hits"] += 1
        print(f"CACHE HIT {url} ({len(html)} bytes)")
        return FetchResult(status=200, html=html, cached=True)

    result = _polite_request(url)
    stats["fetches"] += 1

    if result.status == 200 and result.html is not None:
        cache_file.write_text(result.html, encoding="utf-8")
        print(f"FETCH {url} -> 200 ({len(result.html)} bytes)")
    else:
        print(f"FETCH {url} -> {result.status or 'ERROR'} {result.error or ''}".strip())

    return result