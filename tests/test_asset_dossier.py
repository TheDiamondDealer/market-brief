"""Contract tests for the asset dossier's net-pressure header + tier-ordered evidence
stack (PR-3 Task 1, spec S5.4/S5.5). Pattern follows tests/test_asset_workspace.py and
tests/test_gdelt_impact_chips.py: read the rendered source as text, assert required
markers are present (no DOM execution - this is a static, bundler-free vanilla-JS site).
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class AssetDossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "asset-workspace" / "asset-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "asset-workspace" / "asset-page.css").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(
            ["node", "--check", "site/features/asset-workspace/asset-page.js"],
            cwd=ROOT, check=True, text=True, capture_output=True,
        )

    def test_net_pressure_header_uses_the_pr1_engine(self) -> None:
        self.assertIn("collectDeterministicSignals", self.page)
        self.assertIn("asset-pressure-header", self.page)

    def test_evidence_stack_present_and_tier_ordered(self) -> None:
        self.assertIn("asset-evidence-stack", self.page)
        observed_at = self.page.index("Observed")
        verified_at = self.page.index("Verified")
        ai_at = self.page.index("AI-tagged")
        self.assertLess(observed_at, verified_at, "Observed must render before Verified in source order")
        self.assertLess(verified_at, ai_at, "Verified must render before AI-tagged in source order")

    def test_ai_tier_fetches_the_ledger_with_a_guard(self) -> None:
        self.assertIn("data/impact-tags.json", self.page)
        self.assertIn("try", self.page)
        self.assertIn("catch", self.page)

    def test_honest_empty_states_are_present_not_hidden(self) -> None:
        self.assertIn("No Observed evidence in view", self.page)
        self.assertIn("No Verified evidence in view", self.page)
        self.assertIn("No AI-tagged news for this asset in the current window.", self.page)

    def test_additive_css_does_not_disturb_existing_asset_rules(self) -> None:
        self.assertIn(".asset-pressure-header", self.styles)
        self.assertIn(".asset-evidence-stack", self.styles)
        # Spot-check a couple of pre-existing rules survive untouched.
        self.assertIn(".asset-evidence-column.positive{border-top:3px solid var(--positive)}", self.styles)
        self.assertIn("@media(prefers-reduced-motion:reduce){.asset-workspace *{scroll-behavior:auto!important}}", self.styles)


if __name__ == "__main__":
    unittest.main()
