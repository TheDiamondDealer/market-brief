from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SourceHealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = (SITE / "core" / "freshness.js").read_text(encoding="utf-8")
        cls.page = (SITE / "features" / "source-health" / "source-health-page.js").read_text(encoding="utf-8")
        cls.styles = (SITE / "features" / "source-health" / "source-health-page.css").read_text(encoding="utf-8")
        cls.loader = (SITE / "core" / "feature-loader.js").read_text(encoding="utf-8")

    def test_nested_javascript_is_syntax_valid(self) -> None:
        for path in ("site/core/freshness.js", "site/features/source-health/source-health-page.js"):
            subprocess.run(["node", "--check", path], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_runtime_registry_keeps_source_failures_independent(self) -> None:
        subprocess.run(["node", "tests/js/freshness-registry.test.js"], cwd=ROOT, check=True, text=True, capture_output=True)

    def test_standard_status_and_timestamp_fields_exist(self) -> None:
        for marker in (
            "current",
            "delayed",
            "stale",
            "failed",
            "unavailable",
            "partial",
            "unknown",
            "sourceObservedAt",
            "collectedAt",
            "generatedAt",
            "expectedCadence",
            "lastSuccessfulAt",
            "error",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.core)

    def test_freshness_initialises_before_route_features(self) -> None:
        self.assertIn("script('core/freshness.js')", self.loader)
        self.assertIn(".then(() => Promise.all(manifest.map(loadEntry)))", self.loader)
        self.assertIn("features/source-health/source-health-page.js", self.loader)

    def test_page_exposes_independent_records_and_command_summary(self) -> None:
        for marker in (
            "Observation time, collection time, generation time",
            "A current source cannot conceal a stale or failed neighbour",
            "Source observation",
            "Expected cadence",
            "Last successful run",
            "Unified source registry",
            "Open full source health",
            "router.register('sources'",
            "router.register('source-health'",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.page)

    def test_mobile_accessibility_contract(self) -> None:
        self.assertIn("aria-pressed", self.page)
        self.assertIn("@media(max-width:700px)", self.styles)
        self.assertIn("min-height:42px", self.styles)
        self.assertIn("prefers-reduced-motion", self.styles)
        self.assertIn("overflow-wrap:anywhere", self.styles)


if __name__ == "__main__":
    unittest.main()
