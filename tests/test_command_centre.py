from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class CommandCentreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "command-centre" / "command-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "command-centre" / "command-page.css").read_text(encoding="utf-8")
        cls.daily_styles = (SITE / "features" / "command-centre" / "command-daily.css").read_text(encoding="utf-8")
        cls.base_styles = (SITE / "styles" / "base.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")
        cls.app = (SITE / "app.js").read_text(encoding="utf-8")
        cls.index = (SITE / "index.html").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(["node", "--check", "site/features/command-centre/command-page.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_home_route_loads_command_centre(self) -> None:
        self.assertIn("router.register('home'", self.page)
        self.assertIn("features/command-centre/command-page.js", self.loader)
        self.assertIn("features/command-centre/conflict-watch-data.js", self.loader)
        self.assertIn("features/command-centre/command-page.css", self.loader)
        self.assertIn("features/command-centre/command-daily.css", self.loader)

    def test_daily_brief_is_merged_into_command_centre(self) -> None:
        for marker in ("research.daily", "Daily Brief", "Today’s observed moves", "Five things that matter", "Dominant transmission"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)
        self.assertNotIn('id="view-today"', self.index)
        self.assertNotIn('data-view="today"', self.index)
        self.assertNotIn('data-shell-view="today"', self.index)
        self.assertIn("router.register('today'", self.app)
        self.assertIn("router.navigate('home'", self.app)

    def test_news_direction_chips_explain_expected_pressure(self) -> None:
        self.assertIn("Expected market pressure", self.page)
        self.assertIn("expected directional pressure under the current regime", self.page)
        self.assertIn("market-direction-chip", self.page)
        self.assertIn("market-direction-chip", self.base_styles)
        self.assertIn("command-daily-grid", self.daily_styles)
        self.assertIn("min-width: 0", self.daily_styles)
        self.assertIn("command-table-scroll", self.daily_styles)

    def test_homepage_prioritises_required_surfaces(self) -> None:
        for marker in (
            "Priority market events",
            "Maximum three",
            "Active triggers",
            "Asset decisions and flip conditions",
            "Largest weekly positioning moves",
            "Recent official disclosures",
            "Failures that can change interpretation",
            "From trigger to decision",
            "Conflict and war transmission watch",
            "scheduled every 3 hours",
            "Official-source publications are shown as updates, not independently verified facts",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)
        self.assertIn("slice(0, 3)", self.page)

    def test_composite_scores_are_not_rendered(self) -> None:
        self.assertIn("No composite score shown", self.page)
        self.assertNotIn("risk score", self.page.lower())
        self.assertNotIn("bias.total", self.page)
        self.assertNotIn("confidence-bar", self.page)

    def test_exact_cot_and_political_owner_fields_are_preserved(self) -> None:
        self.assertIn("identityStatus === 'verified'", self.page)
        self.assertIn("cftcContractCode", self.page)
        self.assertIn("trade.owner", self.page)
        self.assertIn("trade.traded", self.page)
        self.assertIn("trade.filed", self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn('scope="col"', self.page)
        self.assertIn('scope="row"', self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("overflow:auto", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)
        self.assertIn("@media (max-width: 700px)", self.daily_styles)

    # --- PR-3 Task 2: home Pressure Board (Today) (spec S5.2) ---------------

    def test_pressure_board_leads_the_home_render_via_the_pr1_engine(self) -> None:
        self.assertIn("collectDeterministicSignals", self.page)
        self.assertIn("pressure-board", self.page)
        self.assertIn('href="#asset/', self.page)
        # The board must be inserted right after the hero verdict and before heroStats().
        # Search render()'s template-literal call sites ("${fn()}"), not the function
        # declarations (which textually precede render() earlier in the file).
        hero_at = self.page.index('<header class="command-hero">')
        board_at = self.page.index("${pressureBoard()}")
        hero_stats_at = self.page.index("${heroStats()}")
        self.assertLess(hero_at, board_at, "Pressure board call must come after the hero markup")
        self.assertLess(board_at, hero_stats_at, "Pressure board call must come before heroStats()")

    def test_pressure_board_degrades_honestly_when_engine_or_board_missing(self) -> None:
        self.assertIn("Pressure board unavailable", self.page)

    def test_top_drivers_ledger_fetch_is_guarded_and_ranked(self) -> None:
        for marker in (
            "Top drivers",
            "top-drivers",
            "data/impact-tags.json",
            "tagState",
            "No AI-tagged drivers in the current window",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)
        self.assertIn("try", self.page)
        self.assertIn("catch", self.page)

    def test_watchpoints_today_section_present(self) -> None:
        self.assertIn("Watchpoints", self.page)

    def test_pressure_board_additive_css_present(self) -> None:
        combined = self.styles + self.daily_styles
        for marker in (".pressure-board", ".pressure-row", ".top-drivers", ".watchpoints"):
            with self.subTest(marker=marker):
                self.assertIn(marker, combined)
        # Spot-check a couple of pre-existing rules survive untouched.
        self.assertIn("command-daily-grid", self.daily_styles)
        self.assertIn("min-width: 0", self.daily_styles)


if __name__ == "__main__":
    unittest.main()
