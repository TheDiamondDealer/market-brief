#!/usr/bin/env python3
"""Collect market-relevant conflict publications from official public RSS feeds."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "site" / "data" / "conflict-watch.json"
JS_PATH = ROOT / "site" / "features" / "command-centre" / "conflict-watch-data.js"
MAX_AGE_DAYS = 14
MAX_ITEMS = 15
MAX_BYTES = 3_000_000

SOURCES = (
    {
        "id": "un-middle-east",
        "name": "United Nations News — Middle East",
        "feedUrl": "https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml",
        "pageUrl": "https://news.un.org/en/news/region/middle-east",
    },
    {
        "id": "us-war-news",
        "name": "U.S. Department of War — News",
        "feedUrl": "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=50",
        "pageUrl": "https://www.war.gov/News/",
    },
    {
        "id": "us-war-releases",
        "name": "U.S. Department of War — Releases",
        "feedUrl": "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=50",
        "pageUrl": "https://www.war.gov/News/Releases/",
    },
)

CONFLICT_TERMS = (
    "war", "conflict", "crisis", "attack", "strike", "missile", "drone", "ceasefire", "de-escalat",
    "escalat", "sanction", "blockade", "nuclear", "combat",
    "security council", "hostilities", "negotiat", "diplomacy", "truce",
)
MARKET_TERMS = (
    "iran", "israel", "gaza", "lebanon", "yemen", "houthi", "red sea", "hormuz", "gulf",
    "iraq", "syria", "ukraine", "russia", "taiwan", "china", "north korea", "venezuela",
    "tanker", "vessel", "oil", "energy", "pipeline", "oil terminal", "shipping", "maritime",
)
TAG_PATTERNS = {
    "Hormuz": ("hormuz",),
    "Red Sea": ("red sea", "houthi"),
    "Iran": ("iran", "iranian"),
    "Israel / Gaza": ("israel", "israeli", "gaza"),
    "Russia / Ukraine": ("russia", "russian", "ukraine", "ukrainian"),
    "Shipping": ("shipping", "maritime", "tanker", "vessel", "oil terminal"),
    "Energy": ("oil", "energy", "pipeline", "terminal"),
    "Sanctions": ("sanction",),
    "Ceasefire / diplomacy": ("ceasefire", "de-escalat", "negotiat", "diplomacy", "truce"),
}
STEM_TERMS = {"de-escalat", "escalat", "sanction", "negotiat", "iran", "israel", "leban", "ukrain", "russia"}


def fetch_xml(url: str) -> bytes:
    user_agent = os.environ.get(
        "CONFLICT_WATCH_USER_AGENT",
        "MarketBriefResearch/2.3 253694733+TheDiamondDealer@users.noreply.github.com",
    )
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=45) as response:
        content_type = str(response.headers.get("Content-Type", "")).lower()
        if not any(value in content_type for value in ("xml", "rss")):
            raise ValueError(f"unexpected content type {content_type or 'missing'}")
        payload = response.read(MAX_BYTES + 1)
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError("empty or oversized RSS response")
    return payload


def clean_text(value: str | None, limit: int = 420) -> str:
    plain = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    plain = " ".join(plain.split())
    if len(plain) <= limit:
        return plain
    return plain[: limit - 1].rsplit(" ", 1)[0] + "…"


def published_at(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OverflowError):
        return None


def has_term(text: str, term: str) -> bool:
    lower = text.lower()
    if term in STEM_TERMS:
        return term in lower
    return bool(re.search(rf"(?<![a-z]){re.escape(term)}(?:s|es|ed|ing)?(?![a-z])", lower))


def relevant(text: str) -> bool:
    return any(has_term(text, term) for term in CONFLICT_TERMS) and any(has_term(text, term) for term in MARKET_TERMS)


def tags_for(text: str) -> list[str]:
    return [label for label, terms in TAG_PATTERNS.items() if any(has_term(text, term) for term in terms)][:5]


def parse_source(source: dict[str, str], payload: bytes, *, now: datetime) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    cutoff = now - timedelta(days=MAX_AGE_DAYS)
    items: list[dict[str, Any]] = []
    for node in root.findall(".//item"):
        title = clean_text(node.findtext("title"), 220)
        summary = clean_text(node.findtext("description")) or "Official source published an update; open the source for full context."
        link = clean_text(node.findtext("link"), 1000)
        stamp = published_at(node.findtext("pubDate"))
        if not title or not link or not stamp:
            continue
        try:
            observed = datetime.fromisoformat(stamp)
        except ValueError:
            continue
        filter_title = re.sub(r"\b(?:(?:department|secretary) of war|war department)\b", "", title, flags=re.IGNORECASE)
        if observed < cutoff or not relevant(filter_title):
            continue
        items.append({
            "id": hashlib.sha256(link.encode("utf-8")).hexdigest()[:16],
            "title": title,
            "summary": summary,
            "publishedAt": stamp,
            "url": link,
            "source": {"id": source["id"], "name": source["name"], "pageUrl": source["pageUrl"]},
            "tags": tags_for(filter_title) or ["Conflict"],
            "dataState": "current",
        })
    return items


def load_previous() -> dict[str, Any]:
    try:
        value = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def collect(previous: dict[str, Any] | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    current_time = now or datetime.now(timezone.utc)
    prior = previous or {}
    prior_by_source: dict[str, list[dict[str, Any]]] = {}
    for item in prior.get("items", []):
        source_id = str(item.get("source", {}).get("id", ""))
        if source_id:
            prior_by_source.setdefault(source_id, []).append(item)

    collected: list[dict[str, Any]] = []
    source_status: list[dict[str, Any]] = []
    failures = 0
    retained = 0
    for source in SOURCES:
        try:
            rows = parse_source(source, fetch_xml(source["feedUrl"]), now=current_time)
            collected.extend(rows)
            source_status.append({
                "id": source["id"], "name": source["name"], "status": "current",
                "itemCount": len(rows), "url": source["pageUrl"], "detail": "Official RSS feed checked successfully.",
            })
        except Exception as exc:
            failures += 1
            fallback_rows = []
            for item in prior_by_source.get(source["id"], []):
                retained_item = dict(item)
                retained_item["dataState"] = "stale-retained"
                fallback_rows.append(retained_item)
            retained += len(fallback_rows)
            collected.extend(fallback_rows)
            source_status.append({
                "id": source["id"], "name": source["name"], "status": "stale-retained" if fallback_rows else "failed",
                "itemCount": len(fallback_rows), "url": source["pageUrl"], "detail": f"Refresh failed: {exc}",
            })

    deduped = {item["url"]: item for item in collected}
    items = sorted(deduped.values(), key=lambda item: item["publishedAt"], reverse=True)[:MAX_ITEMS]
    if failures == len(SOURCES):
        status = "stale-retained" if items else "failed"
    elif failures:
        status = "partial"
    else:
        status = "current"
    return {
        "schemaVersion": 1,
        "generatedAtUtc": current_time.isoformat(timespec="seconds"),
        "sourceMode": "official-publication-watch",
        "collection": {
            "status": status,
            "sourceCount": len(SOURCES),
            "failureCount": failures,
            "retainedItemCount": retained,
            "sourceStatus": source_status,
        },
        "items": items,
        "methodology": (
            "Official-source publication monitor filtered for market-relevant conflict terms. Headlines report what the named source published; "
            "they are not independent verification. Market transmission shown in Command Centre is conditional research analysis."
        ),
    }


def write_dataset(dataset: dict[str, Any], *, dry_run: bool) -> None:
    payload = json.dumps(dataset, ensure_ascii=False, indent=2)
    if dry_run:
        print(payload)
        return
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JS_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(payload + "\n", encoding="utf-8")
    JS_PATH.write_text(
        "window.conflictWatchData = " + json.dumps(dataset, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dataset = collect(load_previous())
    write_dataset(dataset, dry_run=args.dry_run)
    print(
        f"Conflict watch status={dataset['collection']['status']}; "
        f"items={len(dataset['items'])}; failures={dataset['collection']['failureCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
