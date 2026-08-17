import os
from datetime import datetime, timezone

from discover import discover_catalogue_pages, extract_book_urls
from extract import extract_book_records
from normalize import dedupe_by_canonical_url, normalize_record
from report import write_outputs
from fetcher import stats as fetch_stats

BROKEN_URL = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"


def main() -> None:
    started_at = datetime.now(timezone.utc)

    pages = discover_catalogue_pages()
    url_to_source_page = extract_book_urls(pages)
    book_urls = list(url_to_source_page.keys())

    print(f"catalogue_pages={len(pages)} discovered={len(book_urls)} unique_urls={len(book_urls)}")

    if os.environ.get("INJECT_BROKEN_URL"):
        book_urls.append(BROKEN_URL)
        url_to_source_page[BROKEN_URL] = pages[0]["url"]
        print(f"Injected a deliberately broken URL: {BROKEN_URL}")

    raw_records, failures = extract_book_records(book_urls, url_to_source_page)
    print(f"detail_pages={len(book_urls)}")

    valid_books = []
    errors = [{"url": f["url"], "reason": f["reason"]} for f in failures]

    for raw in raw_records:
        result = normalize_record(raw)
        if result["ok"]:
            valid_books.append(result["record"])
        else:
            errors.append({"url": result["url"], "reason": result["reason"]})

    unique_books = dedupe_by_canonical_url(valid_books)

    finished_at = datetime.now(timezone.utc)
    report = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": int((finished_at - started_at).total_seconds() * 1000),
        "catalogue_pages_fetched": len(pages),
        "detail_pages_attempted": len(book_urls),
        "requests_sent": fetch_stats["fetches"],
        "cache_hits": fetch_stats["cache_hits"],
        "valid_records": len(unique_books),
        "invalid_records": len(errors),
        "failed_pages": len(failures),
    }

    write_outputs(unique_books, errors, report)

    print(f"valid={len(unique_books)} invalid={len(errors)} failed_pages={len(failures)}")
    print("Run report written to output/run-report.json")


if __name__ == "__main__":
    main()