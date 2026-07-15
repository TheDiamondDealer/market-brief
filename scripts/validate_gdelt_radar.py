#!/usr/bin/env python3
"""Validate the generated GDELT discovery-radar payload."""

from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "site" / "data" / "gdelt-radar.json"
ALLOWED_STATUS = {"current", "partial", "stale", "failed", "unavailable"}
FORBIDDEN_ARTICLE_KEYS = {"body", "content", "articleText", "fullText", "html", "apiKey", "token", "secret"}


def fail(message: str) -> None:
    raise ValueError(message)


def valid_http_url(value: Any) -> bool:
    try:
        parsed = urllib.parse.urlsplit(str(value or ""))
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate(payload: dict[str, Any]) -> None:
    if payload.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    provider = payload.get("provider")
    if not isinstance(provider, dict) or provider.get("id") != "gdelt-doc-2" or provider.get("readOnly") is not True:
        fail("provider must identify the read-only GDELT DOC 2.0 integration")
    collection = payload.get("collection")
    if not isinstance(collection, dict) or collection.get("status") not in ALLOWED_STATUS:
        fail("collection.status is missing or invalid")
    articles = payload.get("articles")
    if not isinstance(articles, list):
        fail("articles must be a list")
    if collection.get("selectedArticleCount") != len(articles):
        fail("selectedArticleCount must equal the article count")
    if len(articles) > 48:
        fail("articles exceeds the 48-item public payload cap")

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for index, article in enumerate(articles):
        if not isinstance(article, dict):
            fail(f"articles[{index}] must be an object")
        forbidden = FORBIDDEN_ARTICLE_KEYS.intersection(article)
        if forbidden:
            fail(f"articles[{index}] contains forbidden fields: {sorted(forbidden)}")
        identifier = str(article.get("id") or "")
        if not identifier or identifier in seen_ids:
            fail(f"articles[{index}] has a missing or duplicate id")
        seen_ids.add(identifier)
        title = str(article.get("title") or "").strip()
        if len(title) < 20 or len(title) > 320:
            fail(f"articles[{index}] title length is invalid")
        url = str(article.get("url") or "")
        if not valid_http_url(url) or url in seen_urls:
            fail(f"articles[{index}] has an invalid or duplicate URL")
        seen_urls.add(url)
        if article.get("sourceTier") != "discovery" or article.get("verificationStatus") != "unverified":
            fail(f"articles[{index}] must remain discovery-only and unverified")
        score = article.get("materialityScore")
        if not isinstance(score, int) or not 0 <= score <= 100:
            fail(f"articles[{index}] materialityScore must be an integer from 0 to 100")
        for field in ("topicIds", "topics", "assets"):
            if not isinstance(article.get(field), list):
                fail(f"articles[{index}].{field} must be a list")

    source_status = payload.get("sourceStatus")
    if not isinstance(source_status, list) or len(source_status) != 1:
        fail("sourceStatus must contain exactly one GDELT source record")
    if source_status[0].get("status") != collection.get("status"):
        fail("sourceStatus and collection status must agree")
    methodology = payload.get("methodology")
    if not isinstance(methodology, dict) or "official" not in str(methodology.get("verification", "")).lower():
        fail("methodology must state the official-source verification rule")


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[0]) if argv else DEFAULT_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            fail("payload root must be an object")
        validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"GDELT radar validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"GDELT radar validation passed: {len(payload['articles'])} articles, status {payload['collection']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
