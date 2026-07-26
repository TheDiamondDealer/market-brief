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

    def test_why_it_matters_expander_present(self) -> None:
        self.assertIn("gdelt-why", self.page)
        self.assertIn("data-gdelt-why", self.page)
        self.assertIn("gdelt-why-panel", self.page)
        self.assertIn("Why it matters", self.page)

    def test_expander_is_accessible_and_honest(self) -> None:
        self.assertIn("aria-expanded", self.page)
        self.assertIn("aria-controls", self.page)
        self.assertIn("· unverified", self.page)  # honesty framing preserved
        self.assertNotIn("real-time", self.page)        # never overclaim liveness

    def test_expander_reads_note_and_tracks_expanded_state(self) -> None:
        self.assertIn("expandedNotes", self.page)        # module-level open-state set
        self.assertIn("whyItMattersMarkup", self.page)   # dedicated builder
        self.assertIn("gdelt-why-prov", self.page)       # provenance line

    def test_why_panel_css_present(self) -> None:
        self.assertIn(".gdelt-why", self.styles)
        self.assertIn(".gdelt-why-panel", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)


if __name__ == "__main__":
    unittest.main()
