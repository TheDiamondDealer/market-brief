from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVALID = ROOT / "tests" / "fixtures" / "invalid"
sys.path.insert(0, str(ROOT / "scripts"))

from validation_helpers import (  # noqa: E402
    ValidationFailure,
    read_json,
    validate_political_semantics,
)


class RequiredGateFailureModeTests(unittest.TestCase):
    def test_broken_javascript_is_rejected(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(INVALID / "broken.js")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SyntaxError", result.stderr)

    def test_malformed_json_is_rejected(self) -> None:
        with self.assertRaises(ValidationFailure):
            read_json(INVALID / "malformed.json")

    def test_empty_retained_political_history_is_rejected(self) -> None:
        data = read_json(INVALID / "political-empty.json")
        with self.assertRaisesRegex(ValidationFailure, "Pelosi retained history"):
            validate_political_semantics(data)

    def test_malformed_political_asset_is_rejected(self) -> None:
        data = read_json(INVALID / "political-malformed.json")
        with self.assertRaisesRegex(ValidationFailure, "Malformed political rows"):
            validate_political_semantics(data)

    def test_repository_ci_dependencies_and_actions_are_pinned(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_ci_pins.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
