import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discover import extract_book_urls
from extract import extract_book_records
from normalize import dedupe_by_canonical_url, normalize_record, price_text_to_number

CATALOGUE_PAGE_HTML = """
<html><body>
<ol class="row">
  <li><article class="product_pod">
    <h3><a href="../book-one_1/index.html" title="Book One">Book One</a></h3>
  </article></li>
  <li><article class="product_pod">
    <h3><a href="../book-one_1/index.html" title="Book One">Book One duplicate link</a></h3>
  </article></li>
</ol>
</body></html>
"""

BOOK_PAGE_WITH_DESCRIPTION = """
<html><body>
<div class="product_page">
  <h1>Book One</h1>
  <p class="price_color">£12.50</p>
  <p class="instock availability">In stock (5 available)</p>
  <p class="star-rating Four"></p>
  <div id="product_description" class="sub-header"><h2>Product Description</h2></div>
  <p>
    A short description with leading and trailing whitespace.
  </p>
</div>
</body></html>
"""

BOOK_PAGE_NO_DESCRIPTION = """
<html><body>
<div class="product_page">
  <h1>Book Two</h1>
  <p class="price_color">£8.00</p>
  <p class="instock availability">In stock (1 available)</p>
  <p class="star-rating One"></p>
</div>
</body></html>
"""


def test_price_text_to_number():
    assert price_text_to_number("£51.77") == 51.77
    assert price_text_to_number("£8.00") == 8.00


def test_relative_urls_become_absolute():
    page_url = "https://books.toscrape.com/catalogue/page-1.html"
    urls = extract_book_urls([{"url": page_url, "html": CATALOGUE_PAGE_HTML}])
    assert all(u.startswith("https://books.toscrape.com/") for u in urls)


def test_duplicate_links_deduped_on_discovery():
    page_url = "https://books.toscrape.com/catalogue/page-1.html"
    urls = extract_book_urls([{"url": page_url, "html": CATALOGUE_PAGE_HTML}])
    assert len(urls) == 1


def test_missing_description_is_none(monkeypatch):
    from fetcher import FetchResult

    monkeypatch.setattr(
        "extract.fetch_and_cache",
        lambda url: FetchResult(status=200, html=BOOK_PAGE_NO_DESCRIPTION, cached=False),
    )
    records, failures = extract_book_records(["https://books.toscrape.com/catalogue/book-two_2/index.html"], {})
    assert failures == []
    assert records[0]["description"] is None


def test_description_whitespace_is_normalized(monkeypatch):
    from fetcher import FetchResult

    monkeypatch.setattr(
        "extract.fetch_and_cache",
        lambda url: FetchResult(status=200, html=BOOK_PAGE_WITH_DESCRIPTION, cached=False),
    )
    records, failures = extract_book_records(["https://books.toscrape.com/catalogue/book-one_1/index.html"], {})
    assert failures == []
    description = records[0]["description"]
    assert description == description.strip()


def test_dedupe_by_canonical_url_keeps_one_per_url():
    records = [
        {"product_url": "https://example.com/a"},
        {"product_url": "https://example.com/a"},
        {"product_url": "https://example.com/b"},
    ]
    assert len(dedupe_by_canonical_url(records)) == 2


def test_malformed_record_fails_validation():
    raw = {
        "title": "",
        "product_url": "https://books.toscrape.com/catalogue/broken_1/index.html",
        "price_text": "not a price",
        "availability_text": "In stock",
        "rating_text": "Three",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-08-17T00:00:00Z",
    }
    result = normalize_record(raw)
    assert result["ok"] is False