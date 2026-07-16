from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class CotInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")
        cls.script = (SITE / "features" / "cot" / "cot-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "cot" / "cot-page.css").read_text(encoding="utf-8")

    def test_feature_assets_are_loaded_by_ordered_manifest(self) -> None:
        self.assertIn("features/cot/cot-page.css", self.loader)
        self.assertIn("features/cot/cot-page.js", self.loader)
        self.assertIn("node.async = false", self.loader)

    def test_feature_javascript_is_syntax_valid(self) -> None:
        subprocess.run(
            ["node", "--check", "site/features/cot/cot-page.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            ["node", "--check", "site/core/feature-loader.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_only_verified_contracts_are_rendered(self) -> None:
        self.assertIn("identityStatus === 'verified'", self.script)
        self.assertIn("cftcContractCode", self.script)
        self.assertIn("contract.marketName", self.script)
        self.assertIn("contract.exchange", self.script)
        self.assertIn("contract.reportType", self.script)
        self.assertIn("contract.category", self.script)
        self.assertIn("Open official CFTC source", self.script)

    def test_reference_dashboard_chart_table_and_history_are_present(self) -> None:
        for marker in (
            "cotWorkspaceSearch",
            "data-cot-category",
            "data-cot-mode",
            "Position distribution",
            "Recent COT data analysis",
            "cot-positioning-svg",
            "cot-chart-long",
            "cot-chart-short",
            "Prev long %",
            "Previous net",
            "data-cot-sort",
            "history52",
            "Net position",
            "Long / short",
            "Weekly change",
            "Reference coverage",
            "referenceProductIds",
            "dataState === 'stale-retained'",
            "grains: 'Grains'",
            "softs: 'Softs'",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.script)

    def test_accessibility_and_mobile_contract(self) -> None:
        self.assertIn('role="img"', self.script)
        self.assertIn("<desc", self.script)
        self.assertIn('scope="col"', self.script)
        self.assertIn('scope="row"', self.script)
        self.assertIn('aria-pressed', self.script)
        self.assertIn('tabindex="0"', self.script)
        self.assertIn("event.key === 'Enter'", self.script)
        self.assertIn("prefers-reduced-motion", self.script)
        self.assertIn("@media (max-width: 700px)", self.styles)
        self.assertIn("min-height: 44px", self.styles)
        self.assertIn("overflow: auto", self.styles)


if __name__ == "__main__":
    unittest.main()
