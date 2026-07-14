from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class MacroMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "macro-monitor" / "macro-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "macro-monitor" / "macro-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(["node", "--check", "site/features/macro-monitor/macro-page.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_macro_and_rates_routes_are_preserved(self) -> None:
        self.assertIn("router.register('rates'", self.page)
        self.assertIn("router.register('macro'", self.page)
        self.assertIn("features/macro-monitor/macro-page.js", self.loader)
        self.assertIn("features/macro-monitor/macro-page.css", self.loader)

    def test_required_groups_and_connected_series_are_explicit(self) -> None:
        for marker in (
            "Rates & liquidity",
            "Inflation & real yields",
            "Credit",
            "US dollar",
            "Employment & growth",
            "DFF",
            "SOFR",
            "DGS10",
            "DFII10",
            "T10YIE",
            "BAMLH0A0HYM2",
            "DTWEXBGS",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_missing_growth_data_is_not_backfilled_with_estimates(self) -> None:
        self.assertIn("No approved automated employment or growth series is connected yet", self.page)
        self.assertIn("This panel remains empty rather than using estimates or an unsourced proxy", self.page)
        self.assertIn("No approved series connected", self.page)

    def test_series_keep_observation_cadence_source_and_status(self) -> None:
        for marker in (
            "Observation date",
            "Expected cadence",
            "Previous",
            "Series ID",
            "Official FRED series",
            "sourceStatus",
            "row.date",
            "row.sourceUrl",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_sparklines_are_accessible_and_honest(self) -> None:
        self.assertIn('role="img"', self.page)
        self.assertIn('aria-label="${escapeHtml(summary)}"', self.page)
        self.assertIn("previous and latest connected observations", self.page)
        self.assertIn("not a long-history chart", self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("grid-template-columns:1fr", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)
        self.assertIn("overflow", self.styles or "")


if __name__ == "__main__":
    unittest.main()
