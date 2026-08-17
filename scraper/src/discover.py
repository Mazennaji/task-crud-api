from urllib.parse import urljoin

from bs4 import BeautifulSoup

from fetcher import fetch_and_cache

START_URL = "https://books.toscrape.com/index.html"
MAX_PAGES = 3


def discover_catalogue_pages() -> list[dict]:
    pages = []
    current_url = START_URL

    while current_url and len(pages) < MAX_PAGES:
        result = fetch_and_cache(current_url)
        if result.status != 200 or not result.html:
            raise RuntimeError(f"Failed to fetch catalogue page: {current_url} (status {result.status})")

        pages.append({"url": current_url, "html": result.html})

        if len(pages) >= MAX_PAGES:
            break

        soup = BeautifulSoup(result.html, "html.parser")
        next_link = soup.select_one(".next a")
        current_url = urljoin(current_url, next_link["href"]) if next_link else None

    return pages


def extract_book_urls(pages: list[dict]) -> dict[str, str]:
    url_to_source_page: dict[str, str] = {}

    for page in pages:
        soup = BeautifulSoup(page["html"], "html.parser")
        for link in soup.select("article.product_pod h3 a"):
            href = link.get("href")
            if not href:
                continue
            absolute_url = urljoin(page["url"], href)
            if absolute_url not in url_to_source_page:
                url_to_source_page[absolute_url] = page["url"]

    return url_to_source_page