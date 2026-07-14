from __future__ import annotations

import importlib.util
import json
import math
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "update_twelve_data.py"
SPEC = importlib.util.spec_from_file_location("update_twelve_data", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, endpoint, params):
        self.calls.append((endpoint, dict(params)))
        key = (endpoint, params["symbol"])
        value = self.responses[key]
        if isinstance(value, BaseException):
            raise value
        return value


def daily_values(count=260, start=100.0):
    rows = []
    for index in range(count):
        price = start + index
        rows.append({
            "datetime": f"2025-{(index // 28) % 12 + 1:02d}-{index % 28 + 1:02d}",
            "open": str(price - 1),
            "high": str(price + 1),
            "low": str(price - 2),
            "close": str(price),
            "volume": str(1_000_000 + index * 1_000),
        })
    # Ensure lexical sort has unique, monotonically increasing dates.
    from datetime import date, timedelta
    base = date(2025, 1, 1)
    for index, row in enumerate(rows):
        row["datetime"] = (base + timedelta(days=index)).isoformat()
    return rows


class TwelveDataCollectorTests(unittest.TestCase):
    def setUp(self):
        self.item = {
            "id": "nvda",
            "symbol": "NVDA",
            "name": "NVIDIA",
            "exchange": "NASDAQ",
            "apiExchange": None,
            "group": "Semiconductors",
            "currency": "USD",
        }
        self.now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    def test_full_collection_computes_returns_averages_and_trend(self):
        history = daily_values()
        quote = {
            "symbol": "NVDA",
            "name": "NVIDIA",
            "exchange": "NASDAQ",
            "currency": "USD",
            "timestamp": 1784030400,
            "close": "360",
            "previous_close": "359",
            "change": "1",
            "percent_change": "0.2786",
            "volume": "1800000",
            "fifty_two_week": {"low": "100", "high": "370"},
        }
        client = FakeClient({
            ("quote", "NVDA"): quote,
            ("time_series", "NVDA"): {"status": "ok", "values": history},
        })
        payload = module.collect_payload([self.item], client=client, previous={}, mode="full", now=self.now)
        row = payload["watchlist"][0]
        self.assertEqual(payload["collection"]["status"], "current")
        self.assertEqual(row["price"], 360.0)
        self.assertEqual(row["previousClose"], 359.0)
        self.assertEqual(row["movingAverages"]["day20"], 349.5)
        self.assertEqual(row["movingAverages"]["day50"], 334.5)
        self.assertEqual(row["movingAverages"]["day200"], 259.5)
        self.assertEqual(row["trend"]["state"], "bullish")
        self.assertAlmostEqual(row["returns"]["week"], round((360 / 354 - 1) * 100, 2))
        self.assertEqual(len(row["history"]), 260)
        self.assertEqual(client.calls[0][0], "quote")
        self.assertEqual(client.calls[1][0], "time_series")
        self.assertNotIn("apikey", client.calls[0][1])

    def test_snapshot_preserves_history_and_refreshes_quote(self):
        previous_row = module.build_record(
            self.item,
            quote={"close": "200", "previous_close": "198", "timestamp": 1700000000},
            history=module.parse_history({"values": daily_values()}),
            now_iso="2026-07-13T12:00:00Z",
        )
        client = FakeClient({
            ("quote", "NVDA"): {
                "close": "205",
                "previous_close": "200",
                "timestamp": 1784030400,
                "volume": "2000000",
            }
        })
        payload = module.collect_payload(
            [self.item],
            client=client,
            previous={"watchlist": [previous_row], "collection": {"lastSuccessfulAt": "2026-07-13T12:00:00Z"}},
            mode="snapshot",
            now=self.now,
        )
        row = payload["watchlist"][0]
        self.assertEqual(row["price"], 205.0)
        self.assertEqual(len(row["history"]), 260)
        self.assertEqual(payload["collection"]["successCount"], 1)

    def test_failed_symbol_retains_previous_verified_row_as_stale(self):
        previous_row = module.blank_record(self.item, "2026-07-13T12:00:00Z", "current", None)
        previous_row["price"] = 123.45
        previous_row["observedAt"] = "2026-07-13T20:00:00Z"
        client = FakeClient({("quote", "NVDA"): module.SourceError("rate limit")})
        payload = module.collect_payload(
            [self.item],
            client=client,
            previous={"watchlist": [previous_row], "collection": {"lastSuccessfulAt": "2026-07-13T12:00:00Z"}},
            mode="snapshot",
            now=self.now,
        )
        row = payload["watchlist"][0]
        self.assertEqual(row["status"], "stale")
        self.assertEqual(row["price"], 123.45)
        self.assertIn("rate limit", row["error"])
        self.assertEqual(payload["collection"]["status"], "failed")
        self.assertEqual(payload["collection"]["lastSuccessfulAt"], "2026-07-13T12:00:00Z")
        self.assertEqual(module.collection_exit_code(payload), 0)


    def test_failed_empty_run_exits_nonzero(self):
        payload = module.disabled_payload([self.item], now=self.now, reason="pending")
        payload["collection"]["status"] = "failed"
        self.assertEqual(module.collection_exit_code(payload), 1)

    def test_disabled_payload_is_explicit_and_has_no_prices(self):
        payload = module.disabled_payload([self.item], now=self.now, reason="private perimeter pending")
        self.assertEqual(payload["collection"]["mode"], "disabled")
        self.assertEqual(payload["provider"]["licenseMode"], "private-internal-use-only")
        self.assertIsNone(payload["watchlist"][0]["price"])
        self.assertEqual(payload["watchlist"][0]["status"], "unavailable")

    def test_sanitize_error_removes_query_with_api_key(self):
        value = module.sanitize_error("https://api.twelvedata.com/quote?symbol=NVDA&apikey=SECRET")
        self.assertNotIn("SECRET", value)
        self.assertNotIn("apikey", value.lower())

    def test_watchlist_rejects_duplicate_provider_identity(self):
        with self.assertRaises(module.SourceError):
            module.validate_watchlist({"symbols": [
                self.item,
                {**self.item, "id": "duplicate"},
            ]})


if __name__ == "__main__":
    unittest.main()
