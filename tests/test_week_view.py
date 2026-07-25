"""Contract tests for the Week view (#week) - trailing-7d board grammar + a
day-by-day digest + this week's COT shifts + crowd swings + the week ahead
(PR-3 Task 3, spec S5.3). Pattern follows tests/test_asset_dossier.py and
tests/test_command_centre.py: read the rendered source as text, assert
required markers are present (no DOM execution - this is a static,
bundler-free vanilla-JS site).
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class WeekViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (SITE / "features" / "week" / "week-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "week" / "week-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        subprocess.run(
            ["node", "--check", "site/features/week/week-page.js"],
            cwd=ROOT, check=True, text=True, capture_output=True,
        )

    def test_feature_manifest_loads_week_assets(self) -> None:
        self.assertIn("route: 'week'", self.loader)
        self.assertIn("features/week/week-page.js", self.loader)
        self.assertIn("features/week/week-page.css", self.loader)

    def test_week_route_registers_and_reuses_the_existing_host(self) -> None:
        # #view-week + the 'week' nav button already exist in index.html (legacy
        # static recap wired up by app.js) - this feature must register its own
        # handler (superseding the legacy one) and reuse the existing host node,
        # not create a second one or touch nav/index.html.
        self.assertIn("router.register('week'", self.page)
        self.assertIn("view-week", self.page)

    def test_pressure_board_is_windowed_to_the_trailing_7_days_via_the_pr1_engine(self) -> None:
        self.assertIn("collectDeterministicSignals", self.page)
        self.assertIn("since", self.page)
        self.assertIn("7*24*3600*1000", self.page)
        self.assertIn("week-board", self.page)
        self.assertIn('href="#asset/', self.page)

    def test_quiet_rows_render_dimmed_not_hidden(self) -> None:
        self.assertIn("net-quiet", self.page)
        self.assertIn("net-${netKey}", self.page)

    def test_day_by_day_digest_present_and_ledger_fetch_is_guarded(self) -> None:
        self.assertIn("Day-by-day digest", self.page)
        self.assertIn("data/impact-tags.json", self.page)
        self.assertIn("try", self.page)
        self.assertIn("catch", self.page)
        self.assertIn("tagState", self.page)

    def test_cot_shifts_section_present_and_sourced_from_the_collected_result(self) -> None:
        self.assertIn("COT shifts", self.page)
        self.assertIn("source === 'cot'", self.page)

    def test_crowd_swings_section_present_and_ranked_largest_first(self) -> None:
        self.assertIn("Crowd swings", self.page)
        self.assertIn("source === 'crowd'", self.page)
        self.assertIn("crowdSwingMagnitude", self.page)

    def test_week_ahead_section_present_and_degrades_honestly(self) -> None:
        self.assertIn("Week ahead", self.page)
        self.assertIn("marketCalendarData", self.page)
        self.assertIn("Calendar releases shown on the Calendar page.", self.page)

    def test_honest_empty_states_are_present_not_hidden(self) -> None:
        self.assertIn("Week pressure board unavailable", self.page)
        self.assertIn("No AI-tagged headline landed in the trailing 7-day window", self.page)
        self.assertIn("No COT-source position shift landed in the trailing 7 days.", self.page)
        self.assertIn("No prediction-market swing of 5 points or more landed in the trailing 7 days.", self.page)

    def test_sections_render_in_grammar_order(self) -> None:
        # Board -> day digest -> COT shifts -> crowd swings -> week ahead (spec S5.3
        # section order 1-5). Search render()'s template-literal call sites, not the
        # function declarations (which textually precede render() earlier in the file).
        board_at = self.page.index("${weekPressureBoard(buckets)}")
        digest_at = self.page.index("${dayDigest(since)}")
        cot_at = self.page.index("${cotShifts(buckets)}")
        crowd_at = self.page.index("${crowdSwings(buckets)}")
        ahead_at = self.page.index("${weekAhead()}")
        self.assertLess(board_at, digest_at, "Pressure board must render before the day digest")
        self.assertLess(digest_at, cot_at, "Day digest must render before COT shifts")
        self.assertLess(cot_at, crowd_at, "COT shifts must render before crowd swings")
        self.assertLess(crowd_at, ahead_at, "Crowd swings must render before Week ahead")

    def test_additive_css_reuses_globals_and_adds_only_week_specific_rules(self) -> None:
        self.assertIn(".week-day-card", self.styles)
        self.assertIn(".week-signal-row", self.styles)
        self.assertIn("prefers-reduced-motion: reduce", self.styles)


if __name__ == "__main__":
    unittest.main()
