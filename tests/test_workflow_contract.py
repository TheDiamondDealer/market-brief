from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowPublishingContractTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (WORKFLOWS / name).read_text(encoding="utf-8")

    def test_all_workflow_yaml_parses(self) -> None:
        for path in sorted(WORKFLOWS.glob("*.yml")):
            with self.subTest(workflow=path.name):
                parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)
                self.assertIn("jobs", parsed)

    def test_required_pull_request_gate_is_stable(self) -> None:
        text = self.read("validate.yml")
        self.assertIn("pull_request:", text)
        self.assertIn("merge_group:", text)
        self.assertIn("offline-validation:", text)
        self.assertIn("python scripts/check_ci_pins.py", text)
        self.assertIn("requirements/ci.txt", text)
        self.assertIn("python -m pip check", text)

    def test_pages_workflow_is_reusable_and_checks_out_requested_ref(self) -> None:
        text = self.read("deploy-pages.yml")
        self.assertIn("workflow_call:", text)
        self.assertIn("ref: ${{ inputs.ref || github.ref }}", text)
        self.assertIn("path: site", text)
        self.assertIn(
            "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e",
            text,
        )
        self.assertIn("pages: write", text)
        self.assertIn("id-token: write", text)

    def test_collectors_validate_before_commit(self) -> None:
        for name in ("update-free-market-data.yml", "update-political-disclosures.yml"):
            with self.subTest(workflow=name):
                text = self.read(name)
                collect = text.index("Collect official")
                validate = text.index("Validate generated output before commit")
                commit = text.index("Commit validated data")
                push = text.index("git push origin HEAD:main")
                self.assertLess(collect, validate)
                self.assertLess(validate, commit)
                self.assertLess(commit, push)
                self.assertIn("python scripts/validate_generated_data.py", text)
                self.assertIn("python scripts/check_ci_pins.py", text)
                self.assertIn("python -m pip check", text)
                self.assertNotIn("continue-on-error: true", text)

    def test_collectors_revalidate_after_rebase_before_push(self) -> None:
        for name in ("update-free-market-data.yml", "update-political-disclosures.yml"):
            with self.subTest(workflow=name):
                text = self.read(name)
                rebase = text.index("git pull --rebase origin main")
                second_validation = text.index("python scripts/validate_generated_data.py", rebase)
                push = text.index("git push origin HEAD:main", second_validation)
                self.assertLess(rebase, second_validation)
                self.assertLess(second_validation, push)

    def test_collectors_share_writer_queue_and_deploy_latest_main(self) -> None:
        for name in ("update-free-market-data.yml", "update-political-disclosures.yml"):
            with self.subTest(workflow=name):
                text = self.read(name)
                self.assertIn("group: generated-data-writer", text)
                self.assertIn("uses: ./.github/workflows/deploy-pages.yml", text)
                self.assertIn("ref: main", text)
                self.assertIn("needs: update", text)

    def test_political_push_trigger_is_narrowed_to_pipeline_files(self) -> None:
        text = self.read("update-political-disclosures.yml")
        self.assertIn("paths:", text)
        self.assertNotIn("paths-ignore:", text)
        self.assertIn("scripts/update_political_disclosures.py", text)
        self.assertIn("schemas/political-disclosures.schema.json", text)
        self.assertIn("requirements/political.txt", text)

    def test_owner_protection_checklist_names_required_check_and_bypass_risk(self) -> None:
        text = (ROOT / "docs" / "REPOSITORY-PROTECTION.md").read_text(encoding="utf-8")
        self.assertIn("offline-validation", text)
        self.assertIn("GitHub Actions", text)
        self.assertIn("Block force pushes", text)
        self.assertIn("Acceptance drill", text)


if __name__ == "__main__":
    unittest.main()
