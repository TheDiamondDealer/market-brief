from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class ImpactFeedInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "impact-feed" / "impact-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "impact-feed" / "impact-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(["node", "--check", "site/features/impact-feed/impact-page.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_contract_loads_before_interface(self) -> None:
        self.assertLess(self.loader.index("impact-data.js"), self.loader.index("impact-page.js"))
        self.assertIn("impact-page.css", self.loader)

    def test_filters_timeline_and_expandable_causal_detail_are_present(self) -> None:
        for marker in (
            "impactAssetSearch",
            "data-impact-category",
            "data-impact-status",
            "impact-timeline",
            "data-impact-expand",
            "Mechanism",
            "Confirmation",
            "Invalidation",
            "magnitude",
            "horizon",
            "confidence",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_state_and_direct_item_routes_are_supported(self) -> None:
        self.assertIn("developing", self.page)
        self.assertIn("confirmed", self.page)
        self.assertIn("resolved", self.page)
        self.assertIn("registerPattern('impact-detail'", self.page)
        self.assertIn("/^news\\/([^/]+)$/", self.page)

    def test_delayed_and_unknown_data_are_not_overstated(self) -> None:
        self.assertIn("not a real-time news wire", self.page)
        self.assertIn("remain marked unclear or not specified", self.page)
        self.assertNotIn("guaranteed", self.page.lower())

    def test_mobile_and_accessibility_contract(self) -> None:
        self.assertIn('aria-expanded', self.page)
        self.assertIn('aria-label="Affected assets"', self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("min-height:44px", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)


if __name__ == "__main__":
    unittest.main()
