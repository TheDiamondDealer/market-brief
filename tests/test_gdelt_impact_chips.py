from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class GdeltImpactChipsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "gdelt-radar" / "gdelt-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "gdelt-radar" / "gdelt-page.css").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(
            ["node", "--check", "site/features/gdelt-radar/gdelt-page.js"],
            cwd=ROOT, check=True, text=True, capture_output=True,
        )

    def test_fetches_impact_tags_ledger(self) -> None:
        self.assertIn("data/impact-tags.json", self.page)

    def test_renders_ai_chip_strip_using_impact_chips(self) -> None:
        self.assertIn("gdelt-ai-chips", self.page)
        self.assertIn("impactChips", self.page)
        self.assertIn("tier: 'ai'", self.page)

    def test_honest_degraded_states_are_present(self) -> None:
        self.assertIn("AI tagging unavailable", self.page)
        self.assertIn("AI tagging pending", self.page)

    def test_additive_css_does_not_disturb_existing_gdelt_tags_rule(self) -> None:
        self.assertIn(".gdelt-tags span", self.styles)  # existing rough-tag rule untouched
        self.assertIn(".gdelt-ai-chips", self.styles)
        self.assertIn(".gdelt-ai-note", self.styles)


if __name__ == "__main__":
    unittest.main()
