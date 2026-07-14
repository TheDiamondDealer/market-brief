from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "cftc" / "exact-contract-identities.json"
sys.path.insert(0, str(ROOT / "scripts"))

import cot_contracts  # noqa: E402
import update_free_data_api as api  # noqa: E402


class CotContractRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = cot_contracts.load_registry()
        cls.contracts = cot_contracts.contracts_by_id(cls.registry)
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.rows = {item["id"]: item["row"] for item in cls.fixture["rows"]}

    def test_registry_has_unique_verified_codes_and_explicit_unavailable_markets(self) -> None:
        verified = cot_contracts.verified_contracts(self.registry)
        identities = {(item["reportType"], item["cftcContractCode"]) for item in verified}
        self.assertEqual(len(identities), len(verified))
        unavailable = {item["id"]: item for item in cot_contracts.unavailable_contracts(self.registry)}
        self.assertEqual(set(unavailable), {"oil-wti", "oil-brent", "gas-us", "gas-uk"})
        self.assertTrue(all(item["acceptedNames"] == [] for item in unavailable.values()))
        self.assertTrue(all(item["cftcContractCode"] is None for item in unavailable.values()))

    def test_unavailable_energy_benchmarks_reject_current_alternatives(self) -> None:
        wti = self.contracts["oil-wti"]
        gas = self.contracts["gas-us"]
        self.assertFalse(cot_contracts.contract_accepts_row(wti, self.rows["oil-wti-ice"]))
        self.assertFalse(cot_contracts.contract_accepts_row(wti, self.rows["oil-wti-financial"]))
        self.assertFalse(cot_contracts.contract_accepts_row(gas, self.rows["gas-us-last-day-financial"]))
        self.assertFalse(cot_contracts.contract_accepts_row(gas, self.rows["gas-us-different-size"]))

    def test_unavailable_energy_benchmarks_are_not_queried(self) -> None:
        verified_ids = {contract["id"] for contract in cot_contracts.verified_contracts(self.registry)}
        self.assertNotIn("oil-wti", verified_ids)
        self.assertNotIn("gas-us", verified_ids)

    def test_ten_year_notes_accept_current_and_historical_names_but_reject_ultra(self) -> None:
        contract = self.contracts["us10y-futures"]
        current = self.rows["us10y-futures"]
        self.assertTrue(cot_contracts.contract_accepts_row(contract, current))

        historical_name = copy.deepcopy(current)
        historical_name["market_and_exchange_names"] = "10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE"
        self.assertTrue(cot_contracts.contract_accepts_row(contract, historical_name))

        self.assertFalse(cot_contracts.contract_accepts_row(contract, self.rows["us10y-ultra"]))

    def test_registry_accepts_official_alphanumeric_contract_codes(self) -> None:
        registry = copy.deepcopy(self.registry)
        gold = next(contract for contract in registry["contracts"] if contract["id"] == "gold")
        gold["cftcContractCode"] = "06765A"
        cot_contracts.validate_registry(registry)

    def test_api_query_is_bound_to_contract_code_not_name_search(self) -> None:
        contract = self.contracts["us10y-futures"]
        with mock.patch.object(api.collector, "fetch_bytes", return_value=b"[]") as fetch:
            self.assertEqual(api.api_rows(contract), [])
        url = fetch.call_args.args[0]
        self.assertIn("cftc_contract_market_code", url)
        self.assertIn("043602", url)
        self.assertNotIn("UST+10Y", url)

    def test_exact_observation_emits_verified_identity(self) -> None:
        contract = self.contracts["us10y-futures"]
        observations = api.observations_from_rows(contract, [self.rows["us10y-futures"]])
        summary = api.collector.summarise_market(contract["id"], contract["label"], observations)
        summary["contract"] = cot_contracts.contract_metadata(contract, summary["market"])
        self.assertEqual(summary["net"], -2004023)
        self.assertTrue(cot_contracts.generated_row_is_verified(summary, self.registry))

    def test_similar_only_treasury_row_leaves_market_unavailable(self) -> None:
        contract = self.contracts["us10y-futures"]
        with self.assertRaisesRegex(ValueError, "no exact registered contract"):
            api.observations_from_rows(contract, [self.rows["us10y-ultra"]])

    def test_freshness_uses_contract_specific_maximum_age(self) -> None:
        as_of = datetime(2026, 7, 14, tzinfo=timezone.utc)
        self.assertTrue(api.is_recent("2026-07-07", 21, as_of=as_of))
        self.assertFalse(api.is_recent("2026-06-20", 21, as_of=as_of))

    def test_unverified_legacy_rows_are_not_retained(self) -> None:
        legacy = {
            "id": "oil-wti",
            "market": "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE",
        }
        self.assertFalse(cot_contracts.generated_row_is_verified(legacy, self.registry))


if __name__ == "__main__":
    unittest.main()
