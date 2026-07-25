#!/usr/bin/env python3
"""Live smoke for the fragile external endpoints this repo depends on.

The data collectors are deliberately FAIL-OPEN: when a source dies they record
``status=failed`` and keep serving the last good snapshot. That is correct for the
public site, but it means a dead endpoint can go unnoticed for a long time — the ASX
``/asx/1/`` JSON API 404'd for *months* before anyone noticed, and the mocked unit
tests stayed green the whole time.

This script hits the REAL endpoints and FAILS LOUDLY (non-zero exit -> red scheduled
run -> GitHub notification) when one is structurally broken. It is intentionally
separate from the data pipeline so it never blocks a deploy; it is an early warning,
not a gate. Shape checks are pure functions so the logic is unit-tested offline.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Callable

USER_AGENT = "MarketBriefResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)"

ASX_URL = "https://asx.api.markitdigital.com/asx-research/1.0/companies/BHP/announcements?itemsPerPage=1"
RBA_URL = "https://www.rba.gov.au/rss/rss-cb-media-releases.xml"
USDA_URL = "https://usda.library.cornell.edu/api/v1/release/findByIdentifier/wasde?latest=true"


def validate_asx(body: bytes) -> str | None:
    """None if the Markit announcements shape is intact, else a reason string."""
    try:
        data = json.loads(body.decode("utf-8-sig", errors="replace"))
    except ValueError:
        return "response was not JSON"
    inner = data.get("data") if isinstance(data, dict) else None
    items = inner.get("items") if isinstance(inner, dict) else None
    if not isinstance(items, list):
        return "data.items missing — the Markit announcements shape changed"
    return None


def validate_rba(body: bytes) -> str | None:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return "response was not valid XML"
    items = [n for n in root.iter() if n.tag.rsplit("}", 1)[-1].lower() == "item"]
    if not items:
        return "no <item> elements — the RBA RSS feed shape changed"
    return None


def validate_usda(body: bytes) -> str | None:
    try:
        data = json.loads(body.decode("utf-8-sig", errors="replace"))
    except ValueError:
        return "response was not JSON"
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list) or not results:
        return "empty/invalid results — the USDA ESMIS shape changed"
    return None


CHECKS: tuple[dict[str, Any], ...] = (
    {"id": "asx-announcements", "url": ASX_URL, "validate": validate_asx},
    {"id": "rba-media-releases", "url": RBA_URL, "validate": validate_rba},
    {"id": "usda-wasde", "url": USDA_URL, "validate": validate_usda},
)


def fetch(url: str, timeout: int = 45) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,application/xml,text/xml;q=0.9,*/*;q=0.5"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def run_check(check: dict[str, Any], fetcher: Callable[[str], bytes], attempts: int = 3) -> str | None:
    """Error string if the endpoint is structurally broken, else None.

    A transport error (incl. a persistent 404 like the retired ASX API) is retried and,
    if it never recovers, reported as unreachable. A successful fetch with a bad SHAPE is
    a deterministic failure and is NOT retried.
    """
    last_transport: str | None = None
    for _ in range(max(1, attempts)):
        try:
            body = fetcher(check["url"])
        except Exception as exc:  # noqa: BLE001 — any transport error is a retry candidate
            last_transport = f"{type(exc).__name__}: {exc}"
            continue
        return check["validate"](body)
    return f"unreachable after {attempts} attempt(s) ({last_transport})"


def main(argv: list[str] | None = None) -> int:
    failures: list[str] = []
    for check in CHECKS:
        error = run_check(check, fetch)
        print(f"[{check['id']}] {'OK' if error is None else 'BROKEN — ' + error}")
        if error is not None:
            failures.append(check["id"])
    if failures:
        print(f"\nLive-endpoint smoke FAILED for: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nAll live source endpoints healthy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
