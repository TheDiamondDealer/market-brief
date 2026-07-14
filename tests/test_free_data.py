from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import update_free_data as free_data  # noqa: E402
from validation_helpers import ValidationFailure, assert_safe_cot_name  # noqa: E402


class FreeDataFixtureTests(unittest.TestCase):
    def test_fred_fixture_uses_latest_non_missing_observation(self) -> None:
        payload = (FIXTURES / "fred" / "DGS10.csv").read_bytes()
        with mock.patch.object(free_data, "fetch_bytes", return_value=payload):
            result = free_data.fetch_fred_series("DGS10")
        self.assertEqual(result["date"], "2026-07-10")
        self.assertEqual(result["value"], 4.56)
        self.assertEqual(result["previous"], 4.51)
        self.assertEqual(result["changeBps"], 5.0)

    def test_cftc_fixture_parses_expected_managed_money_values(self) -> None:
        text = (FIXTURES / "cftc" / "disaggregated.csv").read_text(encoding="utf-8")
        rows = [free_data.normalise_row(row) for row in csv.DictReader(io.StringIO(text))]
        config = {"oil": {"label": "WTI crude oil", "patterns": ["CRUDE OIL, LIGHT SWEET"]}}
        parsed = free_data.extract_observations(rows, config, "disagg")
        self.assertEqual(len(parsed["oil"]), 2)
        exact = next(item for item in parsed["oil"] if "FINANCIAL" not in item.market_name)
        self.assertEqual(exact.long, 210000)
        self.assertEqual(exact.short, 145000)
        self.assertEqual(exact.net, 65000)

    def test_contract_safety_gate_rejects_secondary_variants(self) -> None:
        assert_safe_cot_name("CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE")
        for unsafe in (
            "CRUDE OIL, LIGHT SWEET-WTI FINANCIAL - NEW YORK MERCANTILE EXCHANGE",
            "MICRO WTI CRUDE OIL - NYMEX",
            "ULTRA 10-YEAR U.S. TREASURY NOTE",
        ):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(ValidationFailure):
                    assert_safe_cot_name(unsafe)


if __name__ == "__main__":
    unittest.main()
