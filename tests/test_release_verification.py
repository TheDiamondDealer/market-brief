from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleaseVerificationTests(unittest.TestCase):
    def test_release_route_and_ownership_verification_passes(self) -> None:
        subprocess.run(
            ["python", "scripts/verify_release_routes.py"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_deployment_runs_full_release_validation(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "deploy-pages.yml").read_text(encoding="utf-8")
        for marker in (
            "push:",
            "branches: [main]",
            "find site tests/js -type f -name '*.js'",
            "python scripts/validate_generated_data.py",
            "python scripts/audit_static_site.py",
            "python scripts/verify_release_routes.py",
            "python -m unittest discover -s tests -v",
            "Record deployed commit",
            "Report deployed revision",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, workflow)

    def test_completed_docs_do_not_claim_optional_br20(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        completion = (ROOT / "docs" / "REMODEL-COMPLETE.md").read_text(encoding="utf-8")
        sources = (ROOT / "docs" / "DATA-SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("BR-01 through BR-19 are implemented", readme)
        self.assertIn("BR-20 is optional and has not been started", readme)
        self.assertIn("Not started", completion)
        self.assertIn("Owner-only repository protection", completion)
        self.assertIn("optional BR-20", sources)

    def test_legacy_command_centre_is_only_a_compatibility_shim(self) -> None:
        shim = (ROOT / "site" / "command-centre.js").read_text(encoding="utf-8")
        self.assertIn("commandCentreRetired = true", shim)
        self.assertNotIn("renderRiskGauge", shim)
        self.assertNotIn("riskAngle", shim)
        self.assertNotIn("bias.total", shim)

    def test_architecture_and_runbook_reference_current_controls(self) -> None:
        architecture = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
        runbook = (ROOT / "docs" / "RUNBOOK.md").read_text(encoding="utf-8")
        for marker in (
            "site/core/freshness.js",
            "scripts/audit_static_site.py",
            "scripts/verify_release_routes.py",
            "features/command-centre/command-page.js",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, architecture)
        self.assertIn("Independent live verification", runbook)
        self.assertIn("deployment workflow proves", runbook)
        self.assertIn("GitHub issue #4", runbook)


if __name__ == "__main__":
    unittest.main()
