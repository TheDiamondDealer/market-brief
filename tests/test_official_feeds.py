from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_official_feeds as official  # noqa: E402
import update_official_feeds_resilient as resilient  # noqa: E402


class OfficialFeedCollectorTests(unittest.TestCase):
    def test_bls_month_periods_are_normalized(self) -> None:
        self.assertEqual(official.bls_period("2026", "M07"), "2026-07")
        self.assertIsNone(official.bls_period("2026", "M13"))
        self.assertIsNone(official.bls_period("2026", "Q01"))

    def test_numeric_field_ignores_metadata(self) -> None:
        key, value = official.numeric_field({
            "period": "2026-07-10",
            "series-description": "Weekly stocks",
            "value": "123.4",
            "value-units": "thousand barrels",
        })
        self.assertEqual(key, "value")
        self.assertEqual(value, 123.4)

    def test_sec_acceptance_timestamp_is_normalized(self) -> None:
        self.assertEqual(
            resilient.accepted_at("20260714123456"),
            "2026-07-14T12:34:56Z",
        )
        self.assertEqual(
            resilient.accepted_at("2026-07-14T12:34:56Z"),
            "2026-07-14T12:34:56Z",
        )
        self.assertIsNone(resilient.accepted_at(None))

    def test_complete_bls_data_remains_current_despite_advisory_message(self) -> None:
        config = {
            "series": [{
                "id": "CUSR0000SA0",
                "name": "US CPI all items",
                "group": "Inflation",
                "unit": "index",
                "frequency": "Monthly",
            }]
        }
        response = {
            "status": "REQUEST_SUCCEEDED",
            "message": ["Calculations have been disabled for this request."],
            "Results": {
                "series": [{
                    "seriesID": "CUSR0000SA0",
                    "data": [
                        {"year": "2026", "period": "M06", "value": "325.1", "footnotes": []},
                        {"year": "2026", "period": "M05", "value": "324.0", "footnotes": []},
                    ],
                }]
            },
        }
        captured = {}

        def fake_request(url, *, method="GET", payload=None, **kwargs):
            captured["url"] = url
            captured["method"] = method
            captured["payload"] = payload
            return response

        with patch.object(resilient.base, "request_json", side_effect=fake_request):
            result = resilient.collect_bls_without_unused_calculations(
                config,
                {},
                "2026-07-15T00:00:00Z",
            )
        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 1)
        self.assertNotIn("calculations", captured["payload"])
        self.assertIn("API advisory", result["detail"])

    def test_failure_retains_prior_verified_records_as_stale(self) -> None:
        previous = {
            "sources": [{
                "id": "eia-energy",
                "records": [{"id": "verified-row"}],
                "observedAt": "2026-07-10",
                "collectedAt": "2026-07-11T00:00:00Z",
                "lastSuccessfulAt": "2026-07-11T00:00:00Z",
            }]
        }
        source = official.source_template(
            "eia-energy",
            "EIA",
            "Energy",
            "Free key",
            "https://www.eia.gov/",
            "Weekly",
            "2026-07-15T00:00:00Z",
        )
        result = official.finalise_failure(source, previous, "temporary outage")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["records"], [{"id": "verified-row"}])
        self.assertIn("temporary outage", result["error"])

    def test_missing_key_without_history_is_unavailable(self) -> None:
        source = official.source_template(
            "bea-nipa",
            "BEA",
            "Macro",
            "Free key",
            "https://apps.bea.gov/api/",
            "Quarterly",
            "2026-07-15T00:00:00Z",
        )
        result = official.finalise_failure(
            source,
            {},
            "BEA_API_KEY is not configured",
            unavailable=True,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["records"], [])

    def test_census_time_slots_have_distinct_stable_record_ids(self) -> None:
        config = {
            "datasets": [{
                "id": "marts",
                "name": "Monthly retail trade",
                "group": "Consumption",
                "frequency": "Monthly",
            }]
        }
        response = [
            [
                "cell_value",
                "data_type_code",
                "time_slot_id",
                "category_code",
                "seasonally_adj",
                "time",
            ],
            ["100", "SM", "1", "44X72", "yes", "2026-06"],
            ["200", "SM", "2", "44X72", "yes", "2026-06"],
            ["200", "SM", "2", "44X72", "yes", "2026-06"],
        ]

        with (
            patch.dict("os.environ", {"CENSUS_API_KEY": "test-key"}),
            patch.object(official, "request_json", return_value=response),
            patch.object(official.time, "sleep"),
        ):
            result = official.collect_census(
                config,
                {},
                "2026-07-15T00:00:00Z",
            )

        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(
            {row["id"] for row in result["records"]},
            {"marts-SM-44X72-yes-1", "marts-SM-44X72-yes-2"},
        )

    def test_census_queries_single_months_until_rows_are_available(self) -> None:
        config = {
            "datasets": [{
                "id": "advm3",
                "name": "Advance durable goods",
                "group": "Manufacturing",
                "frequency": "Monthly",
            }]
        }
        headers = [
            "cell_value",
            "data_type_code",
            "time_slot_id",
            "category_code",
            "seasonally_adj",
            "time",
        ]
        urls = []

        def fake_request(url, **kwargs):
            urls.append(url)
            if len(urls) == 1:
                return [headers]
            return [headers, ["100", "VS", "1", "MDM", "yes", "2026-06"]]

        with (
            patch.dict("os.environ", {"CENSUS_API_KEY": "test-key"}),
            patch.object(official, "request_json", side_effect=fake_request),
            patch.object(official.time, "sleep"),
        ):
            result = official.collect_census(
                config,
                {},
                "2026-07-15T00:00:00Z",
            )

        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(len(urls), 2)
        self.assertTrue(all("time=from" not in url for url in urls))
        self.assertTrue(all("for=us%3A%2A" in url for url in urls))

    def test_committed_cache_validates(self) -> None:
        subprocess.run(
            ["python", "scripts/validate_official_feeds.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


class OfficialFeedIntegrationTests(unittest.TestCase):
    def test_feature_manifest_loads_official_feed_assets(self) -> None:
        text = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertIn("route: 'official-feeds'", text)
        self.assertIn("features/official-feeds/official-feeds-data.js", text)
        self.assertIn("features/official-feeds/official-feeds-health.js", text)
        self.assertIn("features/official-feeds/official-feeds-page.js", text)

    def test_source_health_extension_is_idempotent(self) -> None:
        text = (ROOT / "site" / "features" / "official-feeds" / "official-feeds-health.js").read_text(encoding="utf-8")
        self.assertIn("alreadyInjected", text)
        self.assertIn("if (alreadyInjected(base, expected)) return", text)

    def test_workflow_preserves_optional_key_boundaries(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-official-feeds.yml").read_text(encoding="utf-8")
        for name in ("EIA_API_KEY", "BLS_API_KEY", "BEA_API_KEY", "CENSUS_API_KEY"):
            self.assertIn(f"secrets.{name}", workflow)
        self.assertIn("python scripts/update_official_feeds_resilient.py", workflow)
        self.assertIn("python scripts/validate_official_feeds.py", workflow)
        self.assertNotIn("echo $EIA_API_KEY", workflow)

    def test_registry_covers_six_agencies_and_pinned_ciks(self) -> None:
        registry = json.loads(
            (ROOT / "scripts" / "official_feeds_registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(registry) - {"schemaVersion"},
            {"sec", "bls", "eia", "bea", "census", "usgs"},
        )
        self.assertGreaterEqual(len(registry["sec"]["tickers"]), 20)
        self.assertGreaterEqual(len(registry["sec"]["companies"]), 19)
        self.assertEqual(
            len({row["ticker"] for row in registry["sec"]["companies"]}),
            len(registry["sec"]["companies"]),
        )
        self.assertTrue(all(int(row["cik"]) > 0 for row in registry["sec"]["companies"]))
        self.assertGreaterEqual(len(registry["bls"]["series"]), 8)
        self.assertGreaterEqual(len(registry["eia"]["series"]), 7)
        pce = next(row for row in registry["bea"]["tables"] if row["table"] == "T20804")
        self.assertEqual(pce["frequency"], "M")

    def test_sec_and_bls_records_render_chips(self) -> None:
        source = (ROOT / "site" / "features" / "official-feeds" / "official-feeds-page.js").read_text(encoding="utf-8")
        self.assertIn("themeForTicker", source)
        self.assertIn("sec-theme-chip", source)
        self.assertIn("${secThemeChip(record)}", source)   # interpolated into filingCard
        self.assertIn("deriveBlsPrintSignals", source)      # BLS prints delegate to the engine
        self.assertIn("${blsPrintChip(record)}", source)    # interpolated into seriesCard
        # SEC/BLS chips report the owning source's real status, not a hard-coded 'current'
        self.assertIn("sourceStatus: record.sourceStatus || source.status", source)
        self.assertIn("record.sourceStatus || 'current'", source)


if __name__ == "__main__":
    unittest.main()
