from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class AssetWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "asset-workspace" / "asset-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "asset-workspace" / "asset-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(["node", "--check", "site/features/asset-workspace/asset-page.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_asset_and_legacy_product_routes_are_supported(self) -> None:
        self.assertIn("registerPattern('asset-workspace'", self.page)
        self.assertIn("/^asset\\/([^/]+)$/", self.page)
        self.assertIn("registerPattern('product-detail'", self.page)
        self.assertIn("/^product\\/([^/]+)$/", self.page)
        self.assertIn("features/asset-workspace/asset-page.js", self.loader)

    def test_workspace_contains_required_decision_surfaces(self) -> None:
        for marker in (
            "External chart",
            "Evidence supporting upside",
            "Evidence supporting downside",
            "Confirmation and flip conditions",
            "Impact Feed",
            "Event calendar",
            "CFTC positioning",
            "Physical / macro checks",
            "Source dates",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_unavailable_cot_never_uses_a_substitute(self) -> None:
        self.assertIn("cotContractRegistry", self.page)
        self.assertIn("No substitute used", self.page)
        self.assertIn("No verified exact-contract mapping", self.page)
        self.assertIn("oil-brent", self.page)
        self.assertIn("oil-wti", self.page)

    def test_external_chart_is_display_only(self) -> None:
        self.assertIn("TradingView chart", self.page)
        self.assertIn("Display-only external", self.page)
        self.assertIn("does not copy or recalculate", self.page)
        self.assertIn('loading="lazy"', self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn('title="${escapeHtml(item.name)} external market chart"', self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)
        self.assertIn("grid-template-columns:1fr", self.styles)


if __name__ == "__main__":
    unittest.main()
