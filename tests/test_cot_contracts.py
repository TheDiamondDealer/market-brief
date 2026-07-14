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
        self.assertEqual(set(unavailable), {"oil-brent", "gas-uk"})
        self.assertTrue(all(item["acceptedNames"] == [] for item in unavailable.values()))
        self.assertTrue(all(item["cftcContractCode"] is None for item in unavailable.values()))

    def test_wti_requires_exact_nymex_code_and_name(self) -> None:
        contract = self.contracts["oil-wti"]
        exact = self.rows["oil-wti"]
        self.assertTrue(cot_contracts.contract_accepts_row(contract, exact))

        ice_substitute = copy.deepcopy(exact)
        ice_substitute["market_and_exchange_names"] = "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE"
        self.assertFalse(cot_contracts.contract_accepts_row(contract, ice_substitute))

        wrong_code = copy.deepcopy(exact)
        wrong_code["cftc_contract_market_code"] = "000000"
        self.assertFalse(cot_contracts.contract_accepts_row(contract, wrong_code))

    def test_henry_hub_financial_contract_is_not_accepted(self) -> None:
        contract = self.contracts["gas-us"]
        exact = self.rows["gas-us"]
        self.assertTrue(cot_contracts.contract_accepts_row(contract, exact))
        financial = copy.deepcopy(exact)
        financial["market_and_exchange_names"] = "HENRY HUB LAST DAY FIN - NEW YORK MERCANTILE EXCHANGE"
        self.assertFalse(cot_contracts.contract_accepts_row(contract, financial))

    def test_ten_year_notes_reject_ultra_treasury(self) -> None:
        contract = self.contracts["us10y-futures"]
        exact = self.rows["us10y-futures"]
        self.assertTrue(cot_contracts.contract_accepts_row(contract, exact))
        ultra = copy.deepcopy(exact)
        ultra["market_and_exchange_names"] = "ULTRA 10-YEAR U.S. TREASURY NOTE - CHICAGO BOARD OF TRADE"
        self.assertFalse(cot_contracts.contract_accepts_row(contract, ultra))

    def test_api_query_is_bound_to_contract_code_not_name_search(self) -> None:
        contract = self.contracts["oil-wti"]
        with mock.patch.object(api.collector, "fetch_bytes", return_value=b"[]") as fetch:
            self.assertEqual(api.api_rows(contract), [])
        url = fetch.call_args.args[0]
        self.assertIn("cftc_contract_market_code", url)
        self.assertIn("067651", url)
        self.assertNotIn("LIGHT+SWEET", url)

    def test_exact_observation_emits_verified_identity(self) -> None:
        contract = self.contracts["oil-wti"]
        observations = api.observations_from_rows(contract, [self.rows["oil-wti"]])
        summary = api.collector.summarise_market(contract["id"], contract["label"], observations)
        summary["contract"] = cot_contracts.contract_metadata(contract, summary["market"])
        self.assertEqual(summary["net"], 65000)
        self.assertTrue(cot_contracts.generated_row_is_verified(summary, self.registry))

    def test_similar_only_rows_leave_market_unavailable(self) -> None:
        contract = self.contracts["oil-wti"]
        substitute = copy.deepcopy(self.rows["oil-wti"])
        substitute["market_and_exchange_names"] = "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE"
        with self.assertRaisesRegex(ValueError, "no exact registered contract"):
            api.observations_from_rows(contract, [substitute])

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
