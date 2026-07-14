#!/usr/bin/env python3
"""Collect a private internal equity watchlist from Twelve Data.

The collector never exposes the API key to the browser. It writes a validated
JSON cache plus a browser-ready JavaScript cache. Previous verified rows are
retained and marked stale when an individual symbol or the provider fails.

Production collection is deliberately gated by the GitHub Actions workflow:
the repository must be private and the access perimeter must be explicitly
confirmed before credentialed collection can run.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "scripts" / "twelve_data_watchlist.json"
DEFAULT_JSON = ROOT / "site" / "data" / "equity-market-data.json"
DEFAULT_JS = ROOT / "site" / "equity-data.js"
DEFAULT_API_BASE = "https://api.twelvedata.com"
PROVIDER_URL = "https://twelvedata.com/"
USER_AGENT = "MarketBriefPrivateResearch/1.0 (+https://github.com/TheDiamondDealer/market-brief)"
STATUSES = {"current", "delayed", "stale", "failed", "unavailable", "partial", "unknown"}


class SourceError(RuntimeError):
    """Raised for a provider response that cannot be accepted."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "n/a", "na", "-"}:
        return None
    try:
        result = float(text)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    return int(round(number)) if number is not None else None


def rounded(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None and math.isfinite(value) else None


def pct_change(current: float | None, reference: float | None) -> float | None:
    if current is None or reference in (None, 0):
        return None
    return rounded((current / reference - 1) * 100, 2)


def average(values: Iterable[float | None]) -> float | None:
    cleaned = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return sum(cleaned) / len(cleaned) if cleaned else None


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceError(f"Unable to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SourceError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def write_js(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    path.write_text(
        "window.equityMarketData = "
        + text
        + ";\nwindow.dispatchEvent(new CustomEvent('marketbrief:equity-data', "
        "{ detail: window.equityMarketData }));\n",
        encoding="utf-8",
    )


def validate_watchlist(config: dict[str, Any]) -> list[dict[str, Any]]:
    symbols = config.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise SourceError("Twelve Data watchlist must contain at least one symbol")
    ids: set[str] = set()
    identities: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for index, item in enumerate(symbols):
        if not isinstance(item, dict):
            raise SourceError(f"Watchlist item {index} must be an object")
        normalized = {
            "id": str(item.get("id", "")).strip(),
            "symbol": str(item.get("symbol", "")).strip().upper(),
            "name": str(item.get("name", "")).strip(),
            "exchange": str(item.get("exchange", "")).strip(),
            "apiExchange": str(item.get("apiExchange", "")).strip() or None,
            "group": str(item.get("group", "")).strip(),
            "currency": str(item.get("currency", "")).strip().upper(),
        }
        if not all(normalized[key] for key in ("id", "symbol", "name", "exchange", "group", "currency")):
            raise SourceError(f"Watchlist item {index} is missing a required field")
        identity = (normalized["symbol"], normalized["apiExchange"] or "")
        if normalized["id"] in ids:
            raise SourceError(f"Duplicate watchlist id: {normalized['id']}")
        if identity in identities:
            raise SourceError(f"Duplicate provider identity: {identity[0]} {identity[1]}".strip())
        ids.add(normalized["id"])
        identities.add(identity)
        output.append(normalized)
    return output


def sanitize_error(error: BaseException | str) -> str:
    text = str(error)
    # Never preserve a URL query or a token-like value in generated data.
    if "apikey=" in text.lower():
        text = text.split("?", 1)[0]
    return " ".join(text.replace("\n", " ").split())[:500] or "Unknown provider error"


class TwelveDataClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_API_BASE,
        request_interval_seconds: float = 8.1,
        timeout_seconds: float = 45,
    ) -> None:
        if not api_key.strip():
            raise SourceError("TWELVE_DATA_API_KEY is not configured")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.request_interval_seconds = max(0.0, request_interval_seconds)
        self.timeout_seconds = timeout_seconds
        self._last_request_started = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_started
        delay = self.request_interval_seconds - elapsed
        if self._last_request_started and delay > 0:
            time.sleep(delay)
        self._last_request_started = time.monotonic()

    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        self._throttle()
        query = {**params, "apikey": self.api_key}
        url = f"{self.base_url}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise SourceError(f"Twelve Data HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise SourceError(f"Twelve Data network error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise SourceError("Twelve Data request timed out") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceError("Twelve Data returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise SourceError("Twelve Data response root was not an object")
        if str(payload.get("status", "")).lower() == "error" or payload.get("code"):
            code = payload.get("code", "unknown")
            message = payload.get("message") or "Provider returned an error"
            raise SourceError(f"Twelve Data error {code}: {message}")
        return payload


def quote_params(item: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {"symbol": item["symbol"]}
    if item.get("apiExchange"):
        params["exchange"] = item["apiExchange"]
    return params


def time_series_params(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **quote_params(item),
        "interval": "1day",
        "outputsize": 260,
        "order": "ASC",
        "format": "JSON",
    }


def parse_history(payload: dict[str, Any]) -> list[dict[str, Any]]:
    values = payload.get("values")
    if not isinstance(values, list):
        raise SourceError("Twelve Data time_series response has no values array")
    rows: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict):
            continue
        date = str(value.get("datetime", "")).strip()[:10]
        close = safe_float(value.get("close"))
        if not date or close is None:
            continue
        rows[date] = {
            "date": date,
            "open": rounded(safe_float(value.get("open"))),
            "high": rounded(safe_float(value.get("high"))),
            "low": rounded(safe_float(value.get("low"))),
            "close": rounded(close),
            "volume": safe_int(value.get("volume")),
        }
    ordered = [rows[key] for key in sorted(rows)]
    if not ordered:
        raise SourceError("Twelve Data time_series response has no usable daily bars")
    return ordered[-260:]
