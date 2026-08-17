# The polite scraper — Books to Scrape

A small, polite scraping pipeline: downloads the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com), visits all 60 book pages, turns the
HTML into clean, schema-checked JSON, survives a broken page without crashing, and
ends every run with a short report of what happened.

## Target classification

- **Site:** `books.toscrape.com`, part of the `toscrape.com` sandbox family.
- **Why this site is fair game:** the site describes itself as a fictional bookstore
  built specifically for people to practise scraping on, and its homepage explicitly
  invites scraping. It is not a real business and holds no personal data.
- **Scope:** only the first 3 catalogue pages (60 books total) — no other pages,
  categories, or sites are touched.
- **robots.txt result:** run `curl -I https://books.toscrape.com/robots.txt` (or open
  it in a browser) and record what you get here before your first real run. When this
  project was built, the development sandbox's own network egress rules blocked
  outbound requests to `books.toscrape.com` entirely, so the check has to be done
  from wherever you actually run the scraper — write down the real status code
  (or "no robots file found" if it 404s).
- I will not reuse this code on another site without checking its rules and terms first.

## Lane & install

Python 3.10+. From the project root:

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/index.py
```

This fetches the 3 catalogue pages and all 60 book pages, and writes:

- `output/books.json` — 60 validated, unique records
- `output/errors.json` — any records/pages that failed validation or fetch
- `output/run-report.json` — counts and timing for the run

Run it again and you should get the same 60 records, reading mostly from `cache/`.

To prove the failure handling works, run with one made-up book URL injected on
purpose:

```bash
INJECT_BROKEN_URL=1 python src/index.py
```

`output/run-report.json` will show `failed_pages: 1` and `books.json` will still
have the 60 good records.

## Record schema

Each entry in `books.json`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `product_url` | string (URL) | canonical identity of the record |
| `price_gbp` | number | parsed from `price_text` |
| `price_text` | string | raw price as shown on the page, e.g. `"£51.77"` |
| `availability_text` | string | raw stock text |
| `rating_text` | string \| null | `"One"`–`"Five"` |
| `description` | string \| null | `null` when the page has none — never invented |
| `source_page` | string (URL) | which catalogue page linked to this book |
| `fetched_at` | string (ISO 8601) | when this record was fetched |

Records that fail schema validation are written to `output/errors.json` with a
reason instead of `books.json`.

## Politeness rules

- Every real request sends `User-Agent: FlyRankInternshipA9/1.0 (+https://github.com/Mazennaji/internship-scraper)`.
- Every request has an 8-second timeout.
- At least 500ms between real requests to the site (cached pages need no delay).
- Status codes are checked before parsing; only `200` is treated as a page.
- `5xx` errors and network/timeout failures get one retry after a short wait.
  `404` and `403` are never retried.
- Every fetched page is cached to `cache/` (git-ignored) so repeated development
  runs never re-hit the live site.

## Sample run

This is a real `run-report.json` from a full run of this exact code, validated
against a local fixture server that mirrors the site's markup (the development
sandbox this was built in cannot reach `books.toscrape.com` — see the limitation
below). Running against the live site should look the same, with real timings:

```json
{
  "started_at": "2026-08-17T10:30:19.744459+00:00",
  "finished_at": "2026-08-17T10:30:34.941607+00:00",
  "duration_ms": 15197,
  "catalogue_pages_fetched": 3,
  "detail_pages_attempted": 60,
  "requests_sent": 63,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

Why no browser: the price, title, availability, and description are already in
the HTML the server sends on first load — a browser would only add cost with
nothing extra to show for it.

## Honest limitation

This was built and tested in a sandboxed environment whose network egress rules
block direct access to `books.toscrape.com`. Every stage was verified end-to-end
against a local fixture server that serves markup structurally identical to the
real site (same selectors, same pagination pattern, same missing-description
cases), including the idempotent-rerun check and the broken-page injection. It
has not been run against the live site itself — do that once to confirm, then
trust the cache for everything after.

## Ethics note

Use an official API when one exists instead of scraping. Never bypass logins,
paywalls, or explicit blocks — a `403` or `401` is the site saying no, and the
right response is to stop, not to retry harder. Collect only the fields you
actually need, and keep the request rate low enough that a human running the
site would never notice you were there.

## Tests

```bash
python -m pytest tests/ -v
```

7 unit tests covering price normalization, relative→absolute URL resolution,
duplicate-link dedup on discovery, a missing description, description whitespace
trimming, canonical-URL dedup, and a malformed record failing schema validation.