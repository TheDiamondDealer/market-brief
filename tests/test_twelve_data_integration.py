from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class TwelveDataIntegrationTests(unittest.TestCase):
    def test_generated_disabled_cache_matches_schema_and_has_no_credentials(self) -> None:
        data = json.loads((ROOT / "site" / "data" / "equity-market-data.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "equity-market-data.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(data))
        self.assertEqual(errors, [], [error.message for error in errors])
        self.assertEqual(data["collection"]["mode"], "disabled")
        self.assertTrue(all(row["price"] is None for row in data["watchlist"]))
        rendered = json.dumps(data).lower()
        self.assertNotIn("apikey=", rendered)
        self.assertNotIn("twelve_data_api_key", rendered)

    def test_watchlist_has_unique_ids_and_provider_identities(self) -> None:
        config = json.loads((ROOT / "scripts" / "twelve_data_watchlist.json").read_text(encoding="utf-8"))
        ids = [item["id"] for item in config["symbols"]]
        identities = [(item["symbol"], item.get("apiExchange")) for item in config["symbols"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(identities), len(set(identities)))
        groups = {item["group"] for item in config["symbols"]}
        self.assertIn("Semiconductors", groups)
        self.assertIn("Rare Earths & Critical Minerals", groups)
        self.assertIn("Benchmarks & ETFs", groups)

    def test_feature_manifest_loads_generated_data_before_market_watch_page(self) -> None:
        loader = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        entry = "scripts: ['equity-data.js', 'features/market-watch/market-watch-page.js']"
        self.assertIn("route: 'equities'", loader)
        self.assertIn(entry, loader)
        self.assertIn("features/market-watch/market-watch-page.css", loader)

    def test_adapters_and_freshness_register_equity_domain(self) -> None:
        adapters = (ROOT / "site" / "core" / "adapters.js").read_text(encoding="utf-8")
        freshness = (ROOT / "site" / "core" / "freshness.js").read_text(encoding="utf-8")
        self.assertIn("window.equityMarketData", adapters)
        self.assertIn("core.adapters = Object.freeze({ evidence, equities", adapters)
        self.assertIn("function equityRecords()", freshness)
        self.assertIn("family: 'market-prices'", freshness)
        self.assertIn("marketbrief:equity-data", freshness)

    def test_private_collection_workflow_has_all_activation_gates(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-twelve-data.yml").read_text(encoding="utf-8")
        for marker in (
            "github.event.repository.private",
            "PRIVATE_SITE_ACCESS_CONFIRMED",
            "PRIVATE_MARKET_DATA_ENABLED",
            "secrets.TWELVE_DATA_API_KEY",
            "scripts/update_twelve_data.py",
            "tests/test_twelve_data_pipeline.py",
        ):
            self.assertIn(marker, workflow)
        self.assertNotIn("apikey=", workflow.lower())

    def test_public_pages_deployment_stops_after_private_feed_activation(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-pages.yml").read_text(encoding="utf-8")
        self.assertIn("vars.PRIVATE_MARKET_DATA_ENABLED != 'true'", workflow)

    def test_cloudflare_headers_disable_cache_for_private_market_cache(self) -> None:
        headers = (ROOT / "site" / "_headers").read_text(encoding="utf-8")
        self.assertIn("/equity-data.js", headers)
        self.assertIn("/data/equity-market-data.json", headers)
        self.assertGreaterEqual(headers.count("Cache-Control: private, no-store"), 2)
        self.assertIn("X-Robots-Tag: noindex", headers)

    def test_market_watch_route_and_dynamic_navigation_are_present(self) -> None:
        page = (ROOT / "site" / "features" / "market-watch" / "market-watch-page.js").read_text(encoding="utf-8")
        self.assertIn("router.register('equities'", page)
        self.assertIn('data-view="equities"', page)
        self.assertIn("Largest watchlist moves", page)
        self.assertIn("No API credential reaches the browser", page)


if __name__ == "__main__":
    unittest.main()
