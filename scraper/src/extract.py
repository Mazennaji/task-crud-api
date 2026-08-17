from datetime import datetime, timezone

from bs4 import BeautifulSoup

from fetcher import fetch_and_cache

RATING_WORDS = {"Zero", "One", "Two", "Three", "Four", "Five"}


def extract_book_records(book_urls: list[str], source_page_by_url: dict[str, str]) -> tuple[list[dict], list[dict]]:
    records = []
    failures = []

    for url in book_urls:
        result = fetch_and_cache(url)

        if result.status != 200 or not result.html:
            failures.append({"url": url, "reason": result.error or f"fetch returned status {result.status}"})
            continue

        soup = BeautifulSoup(result.html, "html.parser")
        main = soup.select_one(".product_page")

        title = main.find("h1").get_text(strip=True)
        price_text = main.select_one(".price_color").get_text(strip=True)
        availability_text = " ".join(main.select_one(".availability").get_text().split())

        rating_el = main.select_one("p.star-rating")
        rating_word = None
        if rating_el:
            classes = rating_el.get("class", [])
            rating_word = next((c for c in classes if c in RATING_WORDS), None)

        description_header = main.select_one("#product_description")
        description = None
        if description_header:
            description_p = description_header.find_next_sibling("p")
            if description_p:
                description = description_p.get_text(strip=True)

        records.append(
            {
                "title": title,
                "product_url": url,
                "price_text": price_text,
                "availability_text": availability_text,
                "rating_text": rating_word,
                "description": description,
                "source_page": source_page_by_url.get(url),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return records, failures