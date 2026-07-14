from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validation_helpers import (  # noqa: E402
    read_json,
    validate_free_market_semantics,
    validate_political_semantics,
    validate_summary_consistency,
)


class GeneratedDataTests(unittest.TestCase):
    def test_committed_json_matches_versioned_schemas(self) -> None:
        targets = (
            ("free-market-data.json", "free-market-data.schema.json"),
            ("political-disclosures.json", "political-disclosures.schema.json"),
            ("political-disclosures-summary.json", "political-disclosures-summary.schema.json"),
        )
        for data_name, schema_name in targets:
            with self.subTest(data=data_name):
                data = read_json(ROOT / "site" / "data" / data_name)
                schema = read_json(ROOT / "schemas" / schema_name)
                errors = list(Draft202012Validator(schema).iter_errors(data))
                self.assertEqual(errors, [], "\n".join(error.message for error in errors[:10]))

    def test_committed_generated_data_passes_semantic_validation(self) -> None:
        free_data = read_json(ROOT / "site" / "data" / "free-market-data.json")
        political = read_json(ROOT / "site" / "data" / "political-disclosures.json")
        summary = read_json(ROOT / "site" / "data" / "political-disclosures-summary.json")
        validate_free_market_semantics(free_data)
        validate_political_semantics(political)
        validate_summary_consistency(political, summary)

    def test_browser_generated_javascript_has_valid_syntax(self) -> None:
        for path in (ROOT / "site" / "free-data.js", ROOT / "site" / "political-data.js"):
            with self.subTest(path=path.name):
                result = subprocess.run(
                    ["node", "--check", str(path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
