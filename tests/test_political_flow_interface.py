from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class PoliticalFlowInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "political-flow" / "political-page.js").read_text(encoding="utf-8")
        cls.data = (SITE / "features" / "political-flow" / "political-data.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "political-flow" / "political-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_feature_javascript_is_syntax_valid(self) -> None:
        for path in (
            "site/features/political-flow/political-data.js",
            "site/features/political-flow/political-page.js",
        ):
            with self.subTest(path=path):
                subprocess.run(["node", "--check", path], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_interface_loads_after_lazy_data_adapter(self) -> None:
        data_position = self.loader.index("features/political-flow/political-data.js")
        page_position = self.loader.index("features/political-flow/political-page.js")
        self.assertLess(data_position, page_position)
        self.assertIn("features/political-flow/political-page.css", self.loader)

    def test_required_disclosure_fields_and_official_links_are_visible(self) -> None:
        for marker in (
            "Disclosed owner/account",
            "Trade date",
            "Filed",
            "Disclosure lag",
            "Statutory range",
            "Official source",
            "Open filing",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)
        self.assertIn("spouse, dependent or joint-account transaction is not described as a personal trade", self.page)
        self.assertNotIn("member bought", self.page.lower())

    def test_global_and_profile_workflows_are_lazy_and_direct_linkable(self) -> None:
        for marker in (
            "api.searchTickers",
            "api.tracker",
            "api.year",
            "recentFilings",
            "filingLedger",
            "retryableFilings",
            "#trackers/",
            "registerPattern('political-profile'",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)
        for marker in ("manifest", "summary", "tracker", "year", "searchTickers"):
            self.assertIn(marker, self.data)

    def test_source_health_and_unavailable_states_are_explicit(self) -> None:
        for marker in (
            "Failures remain visible and are retried",
            "Prior verified records are retained",
            "Political Flow data unavailable",
            "Annual history unavailable",
            "Ticker index unavailable",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn('scope="col"', self.page)
        self.assertIn('scope="row"', self.page)
        self.assertIn('aria-live="polite"', self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("min-height:44px", self.styles)
        self.assertIn("overflow:auto", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)

    def test_trade_rows_render_theme_chips_with_lag_exclusion(self) -> None:
        source = (ROOT / "site" / "features" / "political-flow" / "political-page.js").read_text(encoding="utf-8")
        self.assertIn("themeForTicker", source)
        self.assertIn("political-theme-chip", source)
        self.assertIn("excluded from net-pressure windows", source)
        # BOTH trade tables must be chipped — the helper alone would satisfy assertIn:
        self.assertEqual(source.count("${themeChip(trade)}"), 2)


if __name__ == "__main__":
    unittest.main()
