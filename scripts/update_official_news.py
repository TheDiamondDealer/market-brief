#!/usr/bin/env python3
"""Merge free ASX announcement and Federal Reserve policy-release metadata.

This collector extends the existing official-feeds cache without replacing its
agency observations. It publishes public headline/link metadata only, preserves
previous verified records on temporary source failure, and does not represent
the public ASX company endpoint as the licensed real-time ComNews product.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "scripts" / "official_news_registry.json"
OUTPUT_PATH = ROOT / "site" / "data" / "official-feeds.json"
USER_AGENT = os.environ.get(
    "OFFICIAL_NEWS_USER_AGENT",
    "MarketBriefResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)",
)
STATUS_VALUES = {"current", "delayed", "stale", "failed", "unavailable", "partial", "unknown"}
BASE_SOURCE_IDS = {
    "sec-edgar",
    "bls-public-data",
    "eia-energy",
    "bea-nipa",
    "census-eits",
    "usgs-minerals",
}
NEWS_SOURCE_IDS = {"asx-announcements", "federal-reserve-policy"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def iso_timestamp(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            parsed = None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_bytes(url: str, timeout: int = 45, accept: str = "application/json,application/xml,text/xml;q=0.9,*/*;q=0.5") -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def request_json(url: str, timeout: int = 45) -> Any:
    return json.loads(request_bytes(url, timeout=timeout).decode("utf-8-sig", errors="replace"))


def source_template(source_id: str, name: str, family: str, access: str, source_url: str, cadence: str, collected_at: str) -> dict[str, Any]:
    return {
        "id": source_id,
        "name": name,
        "family": family,
        "access": access,
        "status": "unknown",
        "observedAt": None,
        "collectedAt": collected_at,
        "lastSuccessfulAt": None,
        "expectedCadence": cadence,
        "sourceUrl": source_url,
        "detail": "",
        "error": None,
        "records": [],
    }


def prior_source(previous: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    return next((row for row in previous.get("sources", []) if row.get("id") == source_id), None)


def finalise_success(source: dict[str, Any], *, status: str = "current", detail: str = "") -> dict[str, Any]:
    source["status"] = status if status in STATUS_VALUES else "unknown"
    source["detail"] = detail
    source["error"] = None
    source["lastSuccessfulAt"] = source["collectedAt"]
    observed = [str(row.get("observedAt") or row.get("releasedAt") or "") for row in source["records"]]
    source["observedAt"] = max((value for value in observed if value), default=source["collectedAt"])
    return source


def finalise_failure(source: dict[str, Any], previous: dict[str, Any], error: Any) -> dict[str, Any]:
    prior = prior_source(previous, source["id"])
    message = clean_text(error)[:600]
    if prior and prior.get("records"):
        source["records"] = prior["records"]
        source["observedAt"] = prior.get("observedAt")
        source["lastSuccessfulAt"] = prior.get("lastSuccessfulAt") or prior.get("collectedAt")
        source["status"] = "stale"
        source["detail"] = f"Retained {len(source['records'])} previously verified records."
    else:
        source["status"] = "failed"
        source["detail"] = "No verified records are currently available."
    source["error"] = message
    return source


def asx_source_url(raw_url: Any, announcement_id: str) -> str:
    value = clean_text(raw_url)
    if value:
        if value.startswith("https://"):
            return value
        return urllib.parse.urljoin("https://www.asx.com.au", value)
    return f"https://www.asx.com.au/asx/1/file/{urllib.parse.quote(announcement_id)}/announcement"


def collect_asx(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template(
        "asx-announcements",
        "ASX public company announcements",
        "Company Filings",
        "Public per-company announcement endpoint; not licensed ComNews",
        config["sourcePage"],
        "Every four hours on weekdays",
        collected_at,
    )
    failures: list[str] = []
    records: list[dict[str, Any]] = []
    successful_tickers = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(config.get("lookbackDays", 45)))
    count = int(config.get("countPerTicker", 12))

    for ticker_value in config.get("tickers", []):
        ticker = str(ticker_value).strip().upper()
        if not re.fullmatch(r"[A-Z0-9]{2,5}", ticker):
            failures.append(f"Invalid ticker {ticker!r}")
            continue
        url = config["endpointTemplate"].format(ticker=urllib.parse.quote(ticker), count=count)
        try:
            payload = request_json(url)
            rows = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                raise ValueError("response did not contain a data array")
            successful_tickers += 1
            for row in rows:
                if not isinstance(row, dict):
                    continue
                issuer_code = clean_text(row.get("issuer_code")).upper()
                if issuer_code and issuer_code != ticker:
                    failures.append(f"{ticker}: issuer mismatch {issuer_code}")
                    continue
                announcement_id = clean_text(row.get("id"))
                headline = clean_text(row.get("header") or row.get("title"))
                if not announcement_id or not headline:
                    continue
                released_at = iso_timestamp(row.get("document_release_date") or row.get("document_date"))
                if released_at:
                    released_dt = datetime.fromisoformat(released_at.replace("Z", "+00:00"))
                    if released_dt < cutoff:
                        continue
                source_url = asx_source_url(row.get("url"), announcement_id)
                records.append(
                    {
                        "id": f"asx-{announcement_id}",
                        "kind": "announcement",
                        "name": headline,
                        "title": headline,
                        "ticker": ticker,
                        "company": clean_text(row.get("issuer_short_name") or row.get("issuer_full_name")) or ticker,
                        "releasedAt": released_at,
                        "filedAt": released_at,
                        "observedAt": released_at,
                        "period": released_at[:10] if released_at else None,
                        "marketSensitive": bool(row.get("market_sensitive")),
                        "announcementType": clean_text(row.get("announcement_type_description")) or "ASX announcement",
                        "pages": row.get("number_of_pages") if isinstance(row.get("number_of_pages"), int) else None,
                        "sourceUrl": source_url,
                    }
                )
        except Exception as exc:
            failures.append(f"{ticker}: {clean_text(exc)[:180]}")
        time.sleep(0.12)

    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        by_id[record["id"]] = record
    source["records"] = sorted(
        by_id.values(),
        key=lambda row: (str(row.get("observedAt") or ""), row["id"]),
        reverse=True,
    )[: int(config.get("maxRecords", 120))]

    if not source["records"]:
        return finalise_failure(
            source,
            previous,
            "; ".join(failures) or "ASX public company endpoints returned no announcement records",
        )
    result = finalise_success(
        source,
        status="partial" if failures else "current",
        detail=(
            f"{len(source['records'])} public announcements across {successful_tickers}/"
            f"{len(config.get('tickers', []))} configured ASX companies; {len(failures)} endpoint or identity failures."
        ),
    )
    result["error"] = "; ".join(failures)[:600] if failures else None
    return result


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def element_text(element: ET.Element, names: set[str]) -> str:
    for child in element.iter():
        if local_name(child.tag) in names:
            value = clean_text(child.text)
            if value:
                return value
    return ""


def entry_link(element: ET.Element) -> str:
    for child in element.iter():
        if local_name(child.tag) != "link":
            continue
        href = clean_text(child.attrib.get("href"))
        if href:
            return href
        text = clean_text(child.text)
        if text:
            return text
    return ""


def parse_feed(payload: bytes, feed: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    items = [node for node in root.iter() if local_name(node.tag) in {"item", "entry"}]
    records: list[dict[str, Any]] = []
    for item in items[: int(feed.get("maxItems", 20))]:
        title = element_text(item, {"title"})
        link = entry_link(item)
        guid = element_text(item, {"guid", "id"})
        published_at = iso_timestamp(element_text(item, {"pubdate", "published", "updated", "date"}))
        if not title or not link or not link.startswith("https://www.federalreserve.gov/"):
            continue
        identity = guid or link
        records.append(
            {
                "id": stable_id("fed", identity),
                "kind": "policy-release",
                "name": title,
                "title": title,
                "group": feed["group"],
                "feedName": feed["name"],
                "publisher": "Board of Governors of the Federal Reserve System",
                "publishedAt": published_at,
                "observedAt": published_at,
                "period": published_at[:10] if published_at else None,
                "sourceUrl": link,
            }
        )
    return records


def collect_fed(config: dict[str, Any], previous: dict[str, Any], collected_at: str) -> dict[str, Any]:
    source = source_template(
        "federal-reserve-policy",
        "Federal Reserve official policy releases",
        "Monetary Policy",
        "Official RSS; no API key",
        config["sourcePage"],
        "Official release cadence; collected every four hours on weekdays",
        collected_at,
    )
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    successful_feeds = 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(config.get("lookbackDays", 60)))

    for feed in config.get("feeds", []):
        try:
            payload = request_bytes(feed["url"], accept="application/rss+xml,application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.5")
            parsed = parse_feed(payload, feed)
            successful_feeds += 1
            for record in parsed:
                observed_at = record.get("observedAt")
                if observed_at:
                    observed_dt = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
                    if observed_dt < cutoff:
                        continue
                records.append(record)
        except Exception as exc:
            failures.append(f"{feed.get('id', 'feed')}: {clean_text(exc)[:180]}")

    by_url: dict[str, dict[str, Any]] = {}
    for record in records:
        current = by_url.get(record["sourceUrl"])
        if current is None or str(record.get("observedAt") or "") > str(current.get("observedAt") or ""):
            by_url[record["sourceUrl"]] = record
    source["records"] = sorted(
        by_url.values(),
        key=lambda row: (str(row.get("observedAt") or ""), row["id"]),
        reverse=True,
    )[: int(config.get("maxRecords", 60))]

    if not source["records"]:
        return finalise_failure(
            source,
            previous,
            "; ".join(failures) or "Federal Reserve RSS feeds returned no release records",
        )
    result = finalise_success(
        source,
        status="partial" if failures else "current",
        detail=(
            f"{len(source['records'])} official releases from {successful_feeds}/"
            f"{len(config.get('feeds', []))} configured Federal Reserve feeds; {len(failures)} feed failures."
        ),
    )
    result["error"] = "; ".join(failures)[:600] if failures else None
    return result


def collection_summary(sources: list[dict[str, Any]]) -> tuple[str, int, int, int]:
    successful = sum(1 for source in sources if source.get("status") in {"current", "partial", "delayed"})
    unavailable = sum(1 for source in sources if source.get("status") == "unavailable")
    failed = sum(1 for source in sources if source.get("status") in {"failed", "stale"})
    if successful == len(sources):
        overall = "current" if all(source.get("status") == "current" for source in sources) else "partial"
    elif successful:
        overall = "partial"
    elif unavailable == len(sources):
        overall = "unavailable"
    else:
        overall = "failed"
    return overall, successful, failed, unavailable


def validate_dataset(data: dict[str, Any]) -> None:
    if data.get("schemaVersion") != 1:
        raise ValueError("schemaVersion must be 1")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
    ids = {str(source.get("id")) for source in sources}
    expected = BASE_SOURCE_IDS | NEWS_SOURCE_IDS
    if ids != expected:
        raise ValueError(f"official source set mismatch after merge: {sorted(ids)}")
    all_record_ids: set[str] = set()
    for source in sources:
        if source.get("status") not in STATUS_VALUES:
            raise ValueError(f"unknown source status: {source.get('id')}={source.get('status')}")
        records = source.get("records")
        if not isinstance(records, list):
            raise ValueError(f"records must be a list for {source.get('id')}")
        for record in records:
            record_id = str(record.get("id") or "")
            if not record_id:
                raise ValueError(f"record without id in {source.get('id')}")
            if record_id in all_record_ids:
                raise ValueError(f"cross-source record id collision: {record_id}")
            all_record_ids.add(record_id)
            url = str(record.get("sourceUrl") or "")
            if not url.startswith("https://"):
                raise ValueError(f"non-HTTPS official record URL: {url}")


def build_dataset(base_data: dict[str, Any], previous: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if base_data.get("schemaVersion") != 1 or not isinstance(base_data.get("sources"), list):
        raise ValueError("base official-feeds cache is missing or invalid")
    base_ids = {str(source.get("id")) for source in base_data["sources"] if source.get("id") not in NEWS_SOURCE_IDS}
    if base_ids != BASE_SOURCE_IDS:
        raise ValueError(f"base official source set mismatch: {sorted(base_ids)}")

    collected_at = utc_now()
    news_sources = [
        collect_asx(registry["asx"], previous, collected_at),
        collect_fed(registry["fed"], previous, collected_at),
    ]
    sources = [source for source in base_data["sources"] if source.get("id") not in NEWS_SOURCE_IDS] + news_sources
    overall, successful, failed, unavailable = collection_summary(sources)
    last_successes = [source.get("lastSuccessfulAt") for source in sources if source.get("lastSuccessfulAt")]
    methodology = dict(base_data.get("methodology") or {})
    methodology.update(
        {
            "asxAnnouncements": "Public per-company ASX announcement metadata and official document links are collected for a configured watchlist. This is not the licensed complete real-time ComNews service.",
            "federalReserveReleases": "Official Federal Reserve RSS headline and link metadata is collected for monetary policy, speeches, testimony, and credit/liquidity or balance-sheet releases.",
            "newsInterpretation": "Official announcement and policy-release records are evidence inputs only; the collector does not infer market direction or investment conclusions.",
        }
    )
    data = {
        **base_data,
        "generatedAtUtc": collected_at,
        "collection": {
            "status": overall,
            "successCount": successful,
            "failureCount": failed,
            "unavailableCount": unavailable,
            "lastSuccessfulAt": max(last_successes) if last_successes else None,
            "errors": [f"{source['name']}: {source['error']}" for source in sources if source.get("error")],
        },
        "sources": sources,
        "methodology": methodology,
    }
    validate_dataset(data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--previous", type=Path, default=None)
    args = parser.parse_args()

    registry = load_json(args.registry, {})
    base_data = load_json(args.output, {})
    previous_path = args.previous or args.output
    previous = load_json(previous_path, base_data)
    if not registry:
        print(f"Unable to load official-news registry: {args.registry}", file=sys.stderr)
        return 1
    try:
        dataset = build_dataset(base_data, previous, registry)
    except Exception as exc:
        print(f"Unable to update official news feeds: {clean_text(exc)}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Official feeds status={dataset['collection']['status']}; "
        f"sources={len(dataset['sources'])}; "
        f"records={sum(len(source['records']) for source in dataset['sources'])}"
    )
    for source in dataset["sources"][-2:]:
        print(f"- {source['id']}: {source['status']} ({len(source['records'])} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
