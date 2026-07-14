from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class NewsImpactContractTests(unittest.TestCase):
    def test_contract_fixture_matches_versioned_schema(self) -> None:
        schema = json.loads((ROOT / "schemas" / "news-impact.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((ROOT / "tests" / "fixtures" / "news-impact" / "contract-v1.json").read_text(encoding="utf-8"))
        errors = sorted(Draft202012Validator(schema).iter_errors(fixture), key=lambda error: list(error.path))
        self.assertEqual(errors, [], "\n".join(error.message for error in errors))

    def test_runtime_legacy_adapter_preserves_meaning_and_marks_unknowns(self) -> None:
        subprocess.run(
            ["node", "tests/js/news-impact-contract.test.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_contract_requires_decision_support_fields(self) -> None:
        schema_text = (ROOT / "schemas" / "news-impact.schema.json").read_text(encoding="utf-8")
        for field in ("direction", "magnitude", "horizon", "confidence", "mechanism", "confirmation", "invalidation"):
            with self.subTest(field=field):
                self.assertIn(f'"{field}"', schema_text)
        adapter = (ROOT / "site" / "features" / "impact-feed" / "impact-data.js").read_text(encoding="utf-8")
        self.assertIn("horizon: 'unclear'", adapter)
        self.assertIn("confidence: 'unclear'", adapter)
        self.assertIn("Invalidation condition was not specified", adapter)
        self.assertNotIn("guaranteed", adapter.lower())

    def test_feature_manifest_loads_contract_before_future_interface(self) -> None:
        loader = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertIn("features/impact-feed/impact-data.js", loader)


if __name__ == "__main__":
    unittest.main()
