from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class CalendarReactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = (SITE / "features" / "calendar" / "calendar-data.js").read_text(encoding="utf-8")
        cls.page = (SITE / "features" / "calendar" / "calendar-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "calendar" / "calendar-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")
        cls.contract = cls.data + "\n" + cls.page

    def test_fixture_matches_versioned_schema(self) -> None:
        schema = json.loads((ROOT / "schemas" / "calendar-events.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((ROOT / "tests" / "fixtures" / "calendar" / "events-v1.json").read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(fixture), key=lambda error: list(error.path))
        self.assertEqual(errors, [], "\n".join(error.message for error in errors))

    def test_adapter_lifecycle_rules(self) -> None:
        subprocess.run(["node", "tests/js/calendar-contract.test.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_data_loads_before_interface_and_js_is_valid(self) -> None:
        self.assertLess(self.loader.index("calendar-data.js"), self.loader.index("calendar-page.js"))
        for path in ("site/features/calendar/calendar-data.js", "site/features/calendar/calendar-page.js"):
            subprocess.run(["node", "--check", path], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_event_workflow_fields_are_visible(self) -> None:
        for marker in (
            "Previous",
            "Consensus",
            "Actual",
            "Pre-event scenarios",
            "Immediate",
            "+1 trading day",
            "+5 trading days",
            "not-sourced",
            "needs-verification",
            "look-ahead bias",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.contract)

    def test_calendar_and_events_routes_are_preserved(self) -> None:
        self.assertIn("router.register('events'", self.page)
        self.assertIn("router.register('calendar'", self.page)
        self.assertIn("registerPattern('calendar-detail'", self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn("aria-expanded", self.page)
        self.assertIn("aria-pressed", self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("min-height:42px", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)

    def test_event_cards_render_watch_chips(self) -> None:
        source = (ROOT / "site" / "features" / "calendar" / "calendar-page.js").read_text(encoding="utf-8")
        self.assertIn("assetByCalendarAlias", source)
        self.assertIn("'watch'", source)
        self.assertIn("Relevant assets were not explicitly named", source)
        self.assertIn("if (!mapped.length) return '';", source)  # honesty fallback is contract-tested
        self.assertIn("watchChips(event) ||", source)  # helper is actually interpolated with its fallback
        self.assertIn("if (seen.has(asset.id)) return;", source)  # watch chips dedupe by board asset (alias collisions)


if __name__ == "__main__":
    unittest.main()
