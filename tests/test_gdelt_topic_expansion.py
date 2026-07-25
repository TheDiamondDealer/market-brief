"""PR-4 slice 1 — GDELT topic-query expansion (design spec §6.1).

Deterministic, offline contract for the discovery-radar topic registry:
- a new `ags-softs` topic (wheat / cocoa / coffee / grain / drought / export ban),
- a gas-specific expansion (TTF / NBP / gas storage / LNG / pipeline),
- `silver` added to `strategic-materials`.

The GDELT `assets` field is discovery-only vocabulary (the AI tagger, not this file,
is what maps news onto the closed board vocabulary), so these assertions only guard
the registry shape and the deterministic keyword→asset mapping.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


update = load_module("update_gdelt_radar", ROOT / "scripts" / "update_gdelt_radar.py")


def bucket(bucket_id: str) -> dict:
    for entry in update.QUERY_BUCKETS:
        if entry["id"] == bucket_id:
            return entry
    raise AssertionError(f"no QUERY_BUCKETS entry with id {bucket_id!r}")


class GdeltTopicRegistryShapeTests(unittest.TestCase):
    def test_every_bucket_is_well_formed(self) -> None:
        seen_ids = set()
        for entry in update.QUERY_BUCKETS:
            for field in ("id", "name", "query"):
                self.assertTrue(str(entry.get(field) or "").strip(), f"{entry.get('id')}.{field} empty")
            self.assertTrue(entry.get("assets"), f"{entry['id']} has no assets")
            self.assertNotIn(entry["id"], seen_ids, "duplicate bucket id")
            seen_ids.add(entry["id"])


class StrategicMaterialsSilverTests(unittest.TestCase):
    def test_silver_added_to_query_and_assets(self) -> None:
        entry = bucket("strategic-materials")
        self.assertIn("silver", entry["query"].lower())
        self.assertIn("silver", entry["assets"])

    def test_existing_materials_are_preserved(self) -> None:
        entry = bucket("strategic-materials")
        for asset in ("rare-earths", "uranium", "copper", "gold", "lithium"):
            self.assertIn(asset, entry["assets"])


class AgsSoftsTopicTests(unittest.TestCase):
    def test_bucket_exists_with_softs_assets(self) -> None:
        entry = bucket("ags-softs")
        for asset in ("wheat", "cocoa", "coffee"):
            self.assertIn(asset, entry["assets"])

    def test_query_covers_the_spec_terms(self) -> None:
        query = bucket("ags-softs")["query"].lower()
        for term in ("wheat", "cocoa", "coffee", "drought", "export ban"):
            self.assertIn(term, query)

    def test_asset_terms_map_softs_headlines(self) -> None:
        self.assertIn("wheat", update.map_assets("black sea wheat export ban lifts grain prices", ()))
        self.assertIn("cocoa", update.map_assets("west africa cocoa shortage deepens", ()))
        self.assertIn("coffee", update.map_assets("brazil arabica coffee frost damage", ()))


class GasMarketsTopicTests(unittest.TestCase):
    def test_bucket_exists_with_gas_assets(self) -> None:
        entry = bucket("gas-markets")
        for asset in ("gas-us", "gas-uk"):
            self.assertIn(asset, entry["assets"])

    def test_query_covers_gas_hub_terms(self) -> None:
        query = bucket("gas-markets")["query"].lower()
        for term in ("ttf", "nbp", "lng", "pipeline"):
            self.assertIn(term, query)

    def test_asset_terms_map_gas_hub_headlines(self) -> None:
        self.assertIn("gas-uk", update.map_assets("european ttf gas prices surge on storage draw", ()))
        self.assertIn("gas-uk", update.map_assets("uk nbp national balancing point spikes", ()))


class GdeltRequestThrottleTests(unittest.TestCase):
    """Adding two buckets (4→6) worsens GDELT's burst rate-limiting; a polite
    inter-request throttle keeps the hourly run 'current'. It must never slow an
    offline/mocked run (every request fails → no sleep)."""

    def test_delay_constant_is_a_small_positive_default(self) -> None:
        self.assertIsInstance(update.INTER_REQUEST_DELAY_SECONDS, float)
        self.assertGreater(update.INTER_REQUEST_DELAY_SECONDS, 0.0)
        self.assertLessEqual(update.INTER_REQUEST_DELAY_SECONDS, 5.0)

    def test_successful_requests_are_spaced(self) -> None:
        with patch.object(update, "request_json", return_value={"articles": []}), \
             patch.object(update, "time") as fake_time:
            update.collect({}, max_records=1, timespan="1h")
        # one throttle between each pair of successful buckets, none after the last
        self.assertEqual(fake_time.sleep.call_count, len(update.QUERY_BUCKETS) - 1)

    def test_all_failing_requests_never_sleep(self) -> None:
        with patch.object(update, "request_json", side_effect=OSError("offline")), \
             patch.object(update, "time") as fake_time:
            update.collect({}, max_records=1, timespan="1h")
        fake_time.sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
