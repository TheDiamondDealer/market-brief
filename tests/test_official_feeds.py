from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_official_feeds as official  # noqa: E402


class OfficialFeedCollectorTests(unittest.TestCase):
    def test_bls_month_periods_are_normalized(self) -> None:
        self.assertEqual(official.bls_period("2026", "M07"), "2026-07")
        self.assertIsNone(official.bls_period("2026", "M13"))
        self.assertIsNone(official.bls_period("2026", "Q01"))

    def test_numeric_field_ignores_metadata(self) -> None:
        key, value = official.numeric_field({"period": "2026-07-10", "series-description": "Weekly stocks", "value": "123.4", "value-units": "thousand barrels"})
        self.assertEqual(key, "value")
        self.assertEqual(value, 123.4)

    def test_failure_retains_prior_verified_records_as_stale(self) -> None:
        previous = {"sources": [{"id": "eia-energy", "records": [{"id": "verified-row"}], "observedAt": "2026-07-10", "collectedAt": "2026-07-11T00:00:00Z", "lastSuccessfulAt": "2026-07-11T00:00:00Z"}]}
        source = official.source_template("eia-energy", "EIA", "Energy", "Free key", "https://www.eia.gov/", "Weekly", "2026-07-15T00:00:00Z")
        result = official.finalise_failure(source, previous, "temporary outage")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["records"], [{"id": "verified-row"}])
        self.assertIn("temporary outage", result["error"])

    def test_missing_key_without_history_is_unavailable(self) -> None:
        source = official.source_template("bea-nipa", "BEA", "Macro", "Free key", "https://apps.bea.gov/api/", "Quarterly", "2026-07-15T00:00:00Z")
        result = official.finalise_failure(source, {}, "BEA_API_KEY is not configured", unavailable=True)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["records"], [])

    def test_committed_seed_validates(self) -> None:
        subprocess.run(["python", "scripts/validate_official_feeds.py"], cwd=ROOT, check=True, capture_output=True, text=True)


class OfficialFeedIntegrationTests(unittest.TestCase):
    def test_feature_manifest_loads_official_feed_assets(self) -> None:
        text = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertIn("route: 'official-feeds'", text)
        self.assertIn("features/official-feeds/official-feeds-data.js", text)
        self.assertIn("features/official-feeds/official-feeds-health.js", text)
        self.assertIn("features/official-feeds/official-feeds-page.js", text)

    def test_workflow_preserves_optional_key_boundaries(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-official-feeds.yml").read_text(encoding="utf-8")
        for name in ("EIA_API_KEY", "BLS_API_KEY", "BEA_API_KEY", "CENSUS_API_KEY"):
            self.assertIn(f"secrets.{name}", workflow)
        self.assertIn("python scripts/update_official_feeds.py", workflow)
        self.assertIn("python scripts/validate_official_feeds.py", workflow)
        self.assertNotIn("echo $EIA_API_KEY", workflow)

    def test_registry_covers_six_agencies(self) -> None:
        registry = json.loads((ROOT / "scripts" / "official_feeds_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(set(registry) - {"schemaVersion"}, {"sec", "bls", "eia", "bea", "census", "usgs"})
        self.assertGreaterEqual(len(registry["sec"]["tickers"]), 20)
        self.assertGreaterEqual(len(registry["bls"]["series"]), 8)
        self.assertGreaterEqual(len(registry["eia"]["series"]), 7)


if __name__ == "__main__":
    unittest.main()
