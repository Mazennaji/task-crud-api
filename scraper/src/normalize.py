import re

from pydantic import ValidationError

from schema import CleanRecord

PRICE_PATTERN = re.compile(r"[\d.]+")


def price_text_to_number(price_text: str) -> float:
    match = PRICE_PATTERN.search(price_text)
    if not match:
        return float("nan")
    return float(match.group())


def normalize_record(raw: dict) -> dict:
    candidate = {**raw, "price_gbp": price_text_to_number(raw["price_text"])}

    try:
        clean = CleanRecord(**candidate)
    except ValidationError as exc:
        reason = "; ".join(f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors())
        return {"ok": False, "reason": reason, "url": raw.get("product_url")}

    return {"ok": True, "record": clean.model_dump(mode="json")}


def dedupe_by_canonical_url(records: list[dict]) -> list[dict]:
    by_url: dict[str, dict] = {}
    for record in records:
        by_url[record["product_url"]] = record
    return list(by_url.values())