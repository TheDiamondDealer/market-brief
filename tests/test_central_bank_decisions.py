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


if __name__ == "__main__":
    unittest.main()
