from __future__ import annotations

import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_central_bank_decisions as cb  # noqa: E402


class CentralBankParsingTests(unittest.TestCase):
    def test_bps_for_label_maps_standard_ladder(self):
        self.assertEqual(cb.bps_for_label("No change"), 0)
        self.assertEqual(cb.bps_for_label("25 bps increase"), 25)
        self.assertEqual(cb.bps_for_label("50+ bps decrease"), -50)
        self.assertIsNone(cb.bps_for_label("garbage"))

    def test_summarise_picks_modal_and_direction(self):
        outcomes = [
            {"label": "No change", "bps": 0, "probability": 0.30},
            {"label": "25 bps increase", "bps": 25, "probability": 0.62},
            {"label": "50+ bps increase", "bps": 50, "probability": 0.08},
        ]
        modal, modal_prob, expected, direction = cb.summarise(outcomes)
        self.assertEqual(modal, "25 bps increase")
        self.assertEqual(modal_prob, 0.62)
        self.assertEqual(direction, "hawkish")
        self.assertIsNotNone(expected)
        self.assertGreater(expected, 0)

    def test_summarise_empty_outcomes(self):
        self.assertEqual(cb.summarise([]), (None, None, None, None))

    def test_summarise_unmapped_modal_is_hold(self):
        # A high-probability outcome whose label isn't in the 5-rung ladder (bps=None)
        # must classify as 'hold' (conservative), not a fabricated direction.
        outcomes = [
            {"label": "75+ bps increase", "bps": None, "probability": 0.80},
            {"label": "No change", "bps": 0, "probability": 0.20},
        ]
        modal, modal_prob, expected, direction = cb.summarise(outcomes)
        self.assertEqual(modal, "75+ bps increase")
        self.assertEqual(direction, "hold")


def _fake_event(slug, title, end, ladder):
    return {
        "slug": slug, "title": title, "endDate": end, "active": True, "closed": False,
        "volume": 50000,
        "markets": [
            {"groupItemTitle": label, "outcomes": "[\"Yes\", \"No\"]",
             "outcomePrices": f"[\"{p}\", \"{round(1 - p, 4)}\"]"}
            for label, p in ladder
        ],
    }


class CentralBankDatasetTests(unittest.TestCase):
    def test_build_dataset_normalizes_a_bank_meeting(self):
        registry = {
            "schemaVersion": 1,
            "provider": {"id": "polymarket", "readOnly": True,
                         "searchEndpoint": "https://x", "documentationUrl": "https://x"},
            "discovery": {"searchLimitPerType": 30, "historyDays": 90},
            "banks": [{"id": "rba", "name": "Reserve Bank of Australia", "currency": "AUD",
                       "boardAssetId": "aud", "flag": "AU",
                       "searchTerms": ["Reserve Bank of Australia Decision"],
                       "titleKeywords": ["reserve bank of australia decision"]}],
        }
        events = {"Reserve Bank of Australia Decision": [
            _fake_event("rba-aug", "Reserve Bank of Australia Decision in August",
                        "2099-08-11T11:59:00Z",
                        [("No change", 0.62), ("25 bps increase", 0.30), ("25 bps decrease", 0.08)])
        ]}
        data = cb.build_dataset(registry, {}, fetcher=lambda ep, term, lim: events.get(term, []))
        self.assertEqual(data["collection"]["status"], "current")
        bank = data["banks"][0]
        self.assertEqual(bank["id"], "rba")
        self.assertEqual(bank["boardAssetId"], "aud")
        meeting = bank["meetings"][0]
        self.assertEqual(meeting["decisionDate"], "2099-08-11")
        self.assertEqual(meeting["modalOutcome"], "No change")
        self.assertEqual(meeting["impliedDirection"], "hold")
        # outcomes are bps-ordered and each carries a one-point history
        self.assertEqual([o["label"] for o in meeting["outcomes"]],
                         ["25 bps decrease", "No change", "25 bps increase"])
        self.assertEqual(len(meeting["outcomes"][0]["history"]), 1)
        cb.validate_output(data)  # must not raise

    def test_build_dataset_retains_previous_on_total_failure(self):
        registry = {"schemaVersion": 1,
                    "provider": {"id": "polymarket", "readOnly": True,
                                 "searchEndpoint": "https://x", "documentationUrl": "https://x"},
                    "discovery": {"historyDays": 90},
                    "banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                               "boardAssetId": "dxy", "flag": "US", "searchTerms": ["Fed Decision"],
                               "titleKeywords": ["fed decision"]}]}
        previous = {"banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                    "boardAssetId": "dxy", "meetings": [{"decisionDate": "2099-07-29",
                    "outcomes": [{"label": "No change", "bps": 0, "probability": 0.7,
                    "probabilityPercent": 70.0, "probabilitySource": "last trade", "history": []}],
                    "modalOutcome": "No change", "modalProbability": 0.7, "expectedBps": 0.0,
                    "impliedDirection": "hold", "liquidityUsd": 0, "marketUrl": "https://x"}]}],
                    "collection": {"lastSuccessfulAt": "2026-07-25T00:00:00Z"}}

        def boom(ep, term, lim):
            raise RuntimeError("network down")

        data = cb.build_dataset(registry, previous, fetcher=boom)
        self.assertEqual(data["collection"]["status"], "stale")
        self.assertTrue(data["collection"]["error"])
        self.assertEqual(data["banks"][0]["meetings"][0]["decisionDate"], "2099-07-29")

    def test_empty_message_exception_marks_stale_not_current(self):
        registry = {"schemaVersion": 1,
                    "provider": {"id": "polymarket", "readOnly": True,
                                 "searchEndpoint": "https://x", "documentationUrl": "https://x"},
                    "discovery": {"historyDays": 90},
                    "banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                               "boardAssetId": "dxy", "flag": "US", "searchTerms": ["Fed Decision"],
                               "titleKeywords": ["fed decision"]}]}
        previous = {"banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                    "boardAssetId": "dxy", "meetings": [{"decisionDate": "2099-07-29",
                    "outcomes": [{"label": "No change", "bps": 0, "probability": 0.7,
                    "probabilityPercent": 70.0, "probabilitySource": "last trade", "history": []}],
                    "modalOutcome": "No change", "modalProbability": 0.7, "expectedBps": 0.0,
                    "impliedDirection": "hold", "liquidityUsd": 0, "marketUrl": "https://x"}]}],
                    "collection": {"lastSuccessfulAt": "2026-07-25T00:00:00Z"}}

        def boom_no_message(ep, term, lim):
            raise RuntimeError()  # str(exc) == ""

        data = cb.build_dataset(registry, previous, fetcher=boom_no_message)
        self.assertEqual(data["collection"]["status"], "stale")
        self.assertTrue(data["collection"]["error"])
        self.assertEqual(data["collection"]["lastSuccessfulAt"], "2026-07-25T00:00:00Z")

    def test_invalid_retained_data_degrades_to_failed_without_crashing(self):
        registry = {"schemaVersion": 1,
                    "provider": {"id": "polymarket", "readOnly": True,
                                 "searchEndpoint": "https://x", "documentationUrl": "https://x"},
                    "discovery": {"historyDays": 90},
                    "banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                               "boardAssetId": "dxy", "flag": "US", "searchTerms": ["Fed Decision"],
                               "titleKeywords": ["fed decision"]}]}
        previous = {"banks": [{"id": "fed", "name": "Federal Reserve", "currency": "USD",
                    "boardAssetId": "dxy", "meetings": [{"decisionDate": "2099-07-29",
                    "outcomes": [{"label": "No change", "bps": 0, "probability": 1.5,
                    "probabilityPercent": 150.0, "probabilitySource": "last trade", "history": []}],
                    "modalOutcome": "No change", "modalProbability": 1.5, "expectedBps": 0.0,
                    "impliedDirection": "hold", "liquidityUsd": 0, "marketUrl": "https://x"}]}],
                    "collection": {"lastSuccessfulAt": "2026-07-25T00:00:00Z"}}

        def boom(ep, term, lim):
            raise RuntimeError("network down")

        data = cb.build_dataset(registry, previous, fetcher=boom)  # must not raise
        self.assertEqual(data["collection"]["status"], "failed")
        self.assertEqual(data["banks"], [])
        cb.validate_output(data)


if __name__ == "__main__":
    unittest.main()
