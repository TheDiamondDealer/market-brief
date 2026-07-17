"""Contract tests for the asset-board registry and its emitted browser global."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "scripts" / "asset_board.json"
EMITTED = ROOT / "site" / "asset-board-data.js"
WATCHLIST = ROOT / "scripts" / "twelve_data_watchlist.json"

VALID_KINDS = {"asset", "theme"}
VALID_FAMILIES = {"Energy", "Metals", "Softs/Ags", "Rates/FX", "Indices", "Themes"}
ALLOWED_FIELDS = {
    "id", "label", "kind", "family", "cotId", "rateId", "rateInvert",
    "etfIds", "crowdAliases", "calendarAliases", "memberTickers",
}


class AssetBoardRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.assets = cls.registry["assets"]

    def test_schema_version_and_shape(self) -> None:
        self.assertEqual(self.registry["schemaVersion"], 1)
        self.assertIsInstance(self.assets, list)
        self.assertEqual(len(self.assets), 22)

    def test_ids_unique_and_slug_shaped(self) -> None:
        ids = [a["id"] for a in self.assets]
        self.assertEqual(len(ids), len(set(ids)))
        for asset_id in ids:
            self.assertRegex(asset_id, r"^[a-z0-9]+(-[a-z0-9]+)*$")

    def test_required_fields_and_enums(self) -> None:
        for asset in self.assets:
            self.assertLessEqual(set(asset), ALLOWED_FIELDS, asset["id"])
            self.assertIn(asset["kind"], VALID_KINDS)
            self.assertIn(asset["family"], VALID_FAMILIES)
            self.assertTrue(asset["label"].strip())
            if asset["kind"] == "theme":
                self.assertEqual(asset["family"], "Themes")

    def test_member_tickers_exist_in_watchlist(self) -> None:
        watchlist = json.loads(WATCHLIST.read_text(encoding="utf-8"))
        known = {row["id"] for row in watchlist["symbols"]}
        for asset in self.assets:
            for ticker in asset.get("memberTickers", []):
                self.assertIn(ticker, known, f"{asset['id']} → {ticker}")

    def test_member_tickers_only_on_themes(self) -> None:
        for asset in self.assets:
            if asset.get("memberTickers"):
                self.assertEqual(asset["kind"], "theme", asset["id"])

    def test_official_series_rules_shape(self) -> None:
        rules = self.registry["officialSeriesRules"]
        self.assertEqual(len(rules), 3)
        asset_ids = {a["id"] for a in self.assets}
        for rule in rules:
            self.assertEqual(set(rule), {"seriesId", "seriesName", "assetId", "rule"})
            self.assertIn(rule["assetId"], asset_ids)
            self.assertEqual(rule["rule"], "sign-of-change")

    def test_emitted_file_in_sync(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_asset_board", ROOT / "scripts" / "build_asset_board.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(EMITTED.read_text(encoding="utf-8"), module.emit())


if __name__ == "__main__":
    unittest.main()
