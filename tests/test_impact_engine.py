"""Run the Node-based impact-engine behaviour tests (pattern: test_core_modules.py)."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ImpactEngineNodeTests(unittest.TestCase):
    def test_impact_engine_behaviour_in_node(self) -> None:
        result = subprocess.run(
            ["node", "tests/js/impact-engine.test.js"],
            cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("impact-engine tests passed", result.stdout)

    def test_impact_chips_behaviour_in_node(self) -> None:
        result = subprocess.run(
            ["node", "tests/js/impact-chips.test.js"],
            cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("impact-chips tests passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
