from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StaticProductionAuditTests(unittest.TestCase):
    def test_static_audit_passes_repository(self) -> None:
        subprocess.run(
            ["python", "scripts/audit_static_site.py"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_validation_checks_nested_javascript_and_audit(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        self.assertIn("find site tests/js -type f -name '*.js'", workflow)
        self.assertIn("python scripts/audit_static_site.py", workflow)
        self.assertNotIn("find site -maxdepth 1 -name '*.js'", workflow)

    def test_viewport_focus_motion_and_contrast_contracts(self) -> None:
        css = (ROOT / "site" / "styles" / "hardening.css").read_text(encoding="utf-8")
        for marker in (
            "max-width:1440px",
            "max-width:1024px",
            "max-width:768px",
            "max-width:390px",
            ":focus-visible",
            "min-height:44px",
            "prefers-reduced-motion:reduce",
            "forced-colors:active",
            "overflow-x:auto",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, css)

    def test_hardening_loads_before_feature_routes(self) -> None:
        loader = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertIn("stylesheet('styles/hardening.css')", loader)
        self.assertIn("Promise.all([stylesheet('styles/hardening.css'), script('core/freshness.js')])", loader)
        self.assertLess(loader.index("styles/hardening.css"), loader.index("manifest.map(loadEntry)"))

    def test_payload_and_duplicate_asset_guards_are_explicit(self) -> None:
        audit = (ROOT / "scripts" / "audit_static_site.py").read_text(encoding="utf-8")
        for marker in (
            "FILE_BUDGETS",
            "FEATURE_BUDGET",
            "TOTAL_RUNTIME_BUDGET",
            "Duplicate HTML ids",
            "Duplicate feature script",
            "political-disclosures.json",
            "not lazy loaded",
            "missing a title",
            "rel=noopener/noreferrer",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, audit)


if __name__ == "__main__":
    unittest.main()
