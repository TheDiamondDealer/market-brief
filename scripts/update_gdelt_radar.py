#!/usr/bin/env python3
"""Collect a public, discovery-only headline radar from the GDELT DOC 2.0 API.

The output intentionally contains metadata and outbound links only. GDELT records
are discovery leads, not verified facts, and never overwrite primary-source data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "site" / "data" / "gdelt-radar.json"
API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DOCUMENTATION_URL = "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/"
USER_AGENT = os.environ.get(
    "GDELT_USER_AGENT",
    "MarketBriefResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)",
)
MAX_ARTICLES = 48

QUERY_BUCKETS = (
    {
        "id": "strategic-materials",
        "name": "Strategic materials",
        "query": '("rare earth" OR "critical mineral" OR uranium OR copper OR gold OR lithium)',
        "assets": ("rare-earths", "uranium", "copper", "gold", "lithium"),
    },
    {
        "id": "semiconductors-ai",
        "name": "Semiconductors & AI infrastructure",
        "query": '(semiconductor OR "artificial intelligence" OR "data center" OR HBM OR "advanced packaging")',
        "assets": ("semiconductors", "ai-infrastructure"),
    },
    {
        "id": "macro-policy",
        "name": "Macro, trade & policy",
        "query": '(tariff OR "export control" OR sanction OR inflation OR "central bank" OR recession)',
        "assets": ("rates", "us-dollar", "global-equities"),
    },
    {
        "id": "energy-security",
        "name": "Energy & security",
        "query": '(oil OR LNG OR "natural gas" OR OPEC OR nuclear OR defence OR defense)',
        "assets": ("brent", "wti", "gas-us", "gas-uk", "uranium", "defence"),
    },
)

EXCLUDED_DOMAINS = {
    "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
    "youtube.com", "youtu.be", "pinterest.com",
}
MATERIAL_TERMS = {
    "shutdown": 14,
    "halt": 12,
    "suspend": 12,
    "explosion": 14,
    "strike": 10,
    "sanction": 12,
    "export ban": 16,
    "export control": 14,
    "tariff": 10,
    "acquisition": 10,
    "merger": 10,
    "takeover": 12,
    "capital raising": 10,
    "offering": 7,
    "guidance": 8,
    "production cut": 13,
    "production increase": 8,
    "permit": 7,
    "approval": 8,
    "grant": 7,
    "loan": 6,
    "bankruptcy": 14,
    "default": 14,
    "rate cut": 11,
    "rate hike": 11,
}
ASSET_TERMS = {
    "gold": ("gold", "bullion"),
    "silver": ("silver",),
    "copper": ("copper",),
    "uranium": ("uranium", "nuclear"),
    "rare-earths": ("rare earth", "ndpr", "neodymium", "praseodymium", "dysprosium", "terbium"),
    "lithium": ("lithium", "spodumene"),
    "semiconductors": ("semiconductor", "chip", "nvidia", "amd", "intel", "tsmc", "asml", "hbm"),
    "ai-infrastructure": ("artificial intelligence", "ai data center", "data centre", "data center", "advanced packaging"),
    "brent": ("brent", "opec", "crude oil"),
    "wti": ("wti", "crude oil"),
    "gas-us": ("henry hub", "us natural gas"),
    "gas-uk": ("lng", "european gas", "uk gas", "natural gas"),
    "rates": ("central bank", "interest rate", "rate cut", "rate hike", "inflation", "cpi", "pce"),
    "us-dollar": ("us dollar", "dollar index", "fed", "federal reserve"),
    "defence": ("defence", "defense", "pentagon", "military"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def request_json(url: str, timeout: int = 45) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            raise ValueError(f"Unexpected content type: {content_type}")
        return json.loads(response.read().decode("utf-8-sig", errors="replace"))


def normalized(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def canonical_url(value: Any) -> str | None:
    try:
        parsed = urllib.parse.urlsplit(str(value or "").strip())
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(key, val) for key, val in query if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"}]
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, urllib.parse.urlencode(query), ""))


def domain_from_url(url: str) -> str:
    domain = urllib.parse.urlsplit(url).netloc.lower().split(":", 1)[0]
    return domain[4:] if domain.startswith("www.") else domain


def excluded_domain(domain: str) -> bool:
    return any(domain == item or domain.endswith(f".{item}") for item in EXCLUDED_DOMAINS)


def parse_seen_date(value: Any) -> str | None:
    text = str(value or "").strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    return None


def query_url(query: str, max_records: int, timespan: str) -> str:
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(max_records),
        "format": "json",
        "sort": "HybridRel",
        "timespan": timespan,
    }
    return f"{API_URL}?{urllib.parse.urlencode(params)}"


def map_assets(text: str, defaults: tuple[str, ...]) -> list[str]:
    assets = set(defaults)
    for asset, terms in ASSET_TERMS.items():
        if any(term in text for term in terms):
            assets.add(asset)
    return sorted(assets)


def materiality_score(text: str, topic_count: int, seen_at: str | None) -> int:
    score = min(18, topic_count * 6)
    score += sum(points for term, points in MATERIAL_TERMS.items() if term in text)
    if seen_at:
        try:
            age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(seen_at.replace("Z", "+00:00"))).total_seconds() / 3600
            score += 20 if age_hours <= 2 else 14 if age_hours <= 6 else 8 if age_hours <= 24 else 2
        except ValueError:
            pass
    return max(0, min(100, score))


def article_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]


def normalize_article(raw: dict[str, Any], bucket: dict[str, Any], collected_at: str, previous_by_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    title = re.sub(r"\s+", " ", str(raw.get("title") or "")).strip()
    if len(title) < 20 or len(title) > 320:
        return None
    url = canonical_url(raw.get("url"))
    if not url:
        return None
    domain = domain_from_url(url)
    if excluded_domain(domain):
        return None
    seen_at = parse_seen_date(raw.get("seendate"))
    identifier = article_id(url)
    text = normalized(title)
    assets = map_assets(text, tuple(bucket["assets"]))
    previous = previous_by_id.get(identifier, {})
    return {
        "id": identifier,
        "title": title,
        "url": url,
        "domain": domain,
        "language": str(raw.get("language") or "Unknown").strip() or "Unknown",
        "sourceCountry": str(raw.get("sourcecountry") or "Unknown").strip() or "Unknown",
        "seenAt": seen_at,
        "firstSeenAt": previous.get("firstSeenAt") or seen_at or collected_at,
        "topicIds": [bucket["id"]],
        "topics": [bucket["name"]],
        "assets": assets,
        "materialityScore": materiality_score(text, 1, seen_at),
        "sourceTier": "discovery",
        "verificationStatus": "unverified",
        "verificationNote": "Discovery lead only. Confirm against an official filing, company release, government source or trusted financial wire.",
        "duplicateCount": 1,
    }


def merge_article(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged["topicIds"] = sorted(set(existing.get("topicIds", [])) | set(incoming.get("topicIds", [])))
    merged["topics"] = sorted(set(existing.get("topics", [])) | set(incoming.get("topics", [])))
    merged["assets"] = sorted(set(existing.get("assets", [])) | set(incoming.get("assets", [])))
    merged["materialityScore"] = max(int(existing.get("materialityScore", 0)), int(incoming.get("materialityScore", 0)))
    merged["duplicateCount"] = int(existing.get("duplicateCount", 1)) + 1
    if str(incoming.get("seenAt") or "") > str(existing.get("seenAt") or ""):
        merged["seenAt"] = incoming.get("seenAt")
    return merged


def collect(previous: dict[str, Any], max_records: int = 50, timespan: str = "24h") -> dict[str, Any]:
    collected_at = utc_now()
    previous_articles = [item for item in previous.get("articles", []) if isinstance(item, dict)]
    previous_by_id = {str(item.get("id")): item for item in previous_articles if item.get("id")}
    articles: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    raw_count = 0
    successes = 0

    for bucket in QUERY_BUCKETS:
        try:
            payload = request_json(query_url(str(bucket["query"]), max_records, timespan))
            raw_articles = payload.get("articles", []) if isinstance(payload, dict) else []
            if not isinstance(raw_articles, list):
                raise ValueError("GDELT payload did not contain an articles list")
            successes += 1
            raw_count += len(raw_articles)
            for raw in raw_articles:
                if not isinstance(raw, dict):
                    continue
                item = normalize_article(raw, bucket, collected_at, previous_by_id)
                if not item:
                    continue
                existing = articles.get(item["id"])
                articles[item["id"]] = merge_article(existing, item) if existing else item
        except Exception as exc:
            errors.append(f"{bucket['id']}: {type(exc).__name__}: {exc}")

    selected = sorted(
        articles.values(),
        key=lambda item: (int(item.get("materialityScore", 0)), str(item.get("seenAt") or "")),
        reverse=True,
    )[:MAX_ARTICLES]

    prior_success = previous.get("collection", {}).get("lastSuccessfulAt")
    if successes == len(QUERY_BUCKETS):
        status = "current"
        last_success = collected_at
        error = None
    elif successes > 0:
        status = "partial"
        last_success = collected_at
        error = "; ".join(errors)
    elif previous_articles:
        status = "stale"
        last_success = prior_success
        selected = previous_articles[:MAX_ARTICLES]
        error = "; ".join(errors) or "All GDELT queries failed; retained the previous snapshot."
    else:
        status = "failed"
        last_success = prior_success
        error = "; ".join(errors) or "All GDELT queries failed."

    topics = [{"id": item["id"], "name": item["name"], "query": item["query"]} for item in QUERY_BUCKETS]
    detail = f"{len(selected)} discovery leads selected from {raw_count} returned records across {successes}/{len(QUERY_BUCKETS)} successful queries."
    return {
        "schemaVersion": 1,
        "generatedAtUtc": collected_at,
        "provider": {
            "id": "gdelt-doc-2",
            "name": "GDELT DOC 2.0 API",
            "readOnly": True,
            "documentationUrl": DOCUMENTATION_URL,
        },
        "collection": {
            "status": status,
            "expectedCadence": "Hourly",
            "queryCount": len(QUERY_BUCKETS),
            "successfulQueryCount": successes,
            "rawArticleCount": raw_count,
            "selectedArticleCount": len(selected),
            "lastSuccessfulAt": last_success,
            "error": error,
        },
        "disclaimer": "Unverified discovery radar. A GDELT match is evidence that media coverage exists, not proof that the underlying claim is true or financially material.",
        "topics": topics,
        "articles": selected,
        "sourceStatus": [{
            "id": "gdelt-doc-2",
            "source": "GDELT DOC 2.0 public API",
            "status": status,
            "observationDate": max((str(item.get("seenAt") or "") for item in selected), default=None),
            "lastSuccessfulAt": last_success,
            "expectedCadence": "Hourly",
            "detail": detail,
            "error": error,
            "url": DOCUMENTATION_URL,
        }],
        "methodology": {
            "role": "Discovery and early-warning only",
            "storedFields": "Headline metadata, source domain, timestamps, topic mapping and outbound URL only; no article body text.",
            "verification": "Confirm material claims against an official release, filing, regulator, government source or trusted financial wire.",
            "ranking": "Deterministic relevance, event-term and recency score; not sentiment analysis and not a trading signal.",
        },
    }


def write_output(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--max-records", type=int, default=50)
    parser.add_argument("--timespan", default="24h")
    args = parser.parse_args(argv)
    previous = load_json(args.output, {})
    payload = collect(previous, max_records=max(1, min(args.max_records, 250)), timespan=args.timespan)
    write_output(payload, args.output)
    print(f"GDELT radar: {payload['collection']['status']} — {payload['collection']['selectedArticleCount']} selected")
    if payload["collection"]["status"] == "failed":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
