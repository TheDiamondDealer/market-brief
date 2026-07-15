from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_crowd_expectations_hardened as hardened  # noqa: E402


def record(
    item_id: str,
    category_id: str,
    event: str,
    rank: int,
) -> dict:
    return {
        "id": item_id,
        "categoryId": category_id,
        "eventTitle": event,
        "sourceUrl": f"https://polymarket.com/event/{event}",
        "qualityScore": 100 - rank,
        "relevanceScore": 3,
        "volume24h": 100000 - rank,
        "liquidity": 100000 - rank,
    }


class CrowdSelectionBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (ROOT / "scripts" / "crowd_expectations_registry.json").read_text(
                encoding="utf-8"
            )
        )

    def test_category_reserve_prevents_high_ranked_monopoly(self) -> None:
        registry = json.loads(json.dumps(self.registry))
        registry["discovery"]["maxMarkets"] = 12
        ranked = [
            record(f"macro-{index}", "monetary-policy", f"macro-event-{index}", index)
            for index in range(20)
        ]
        ranked += [
            record(f"energy-{index}", "energy-commodities", f"energy-event-{index}", 30 + index)
            for index in range(4)
        ]
        ranked += [
            record(f"geo-{index}", "geopolitics-security", f"geo-event-{index}", 40 + index)
            for index in range(4)
        ]

        selected = hardened.balanced_selection(ranked, registry)
        counts = {}
        for item in selected:
            counts[item["categoryId"]] = counts.get(item["categoryId"], 0) + 1

        self.assertEqual(len(selected), 12)
        self.assertGreaterEqual(counts.get("energy-commodities", 0), 3)
        self.assertGreaterEqual(counts.get("geopolitics-security", 0), 3)
        self.assertLessEqual(counts.get("monetary-policy", 0), 6)

    def test_event_family_cap_limits_duplicate_outcomes(self) -> None:
        registry = json.loads(json.dumps(self.registry))
        registry["discovery"]["maxMarkets"] = 10
        ranked = [
            record(f"fed-bracket-{index}", "monetary-policy", "fed-july", index)
            for index in range(12)
        ]
        ranked += [
            record(f"fed-september-{index}", "monetary-policy", "fed-september", 20 + index)
            for index in range(6)
        ]

        selected = hardened.balanced_selection(
            ranked,
            registry,
            reserve_per_category=0,
            max_per_category=16,
            max_per_event=4,
        )
        family_counts = {}
        for item in selected:
            family = hardened.event_family(item)
            family_counts[family] = family_counts.get(family, 0) + 1

        self.assertLessEqual(max(family_counts.values()), 4)
        self.assertEqual(len(selected), 8)

    def test_only_already_qualified_candidates_are_selected(self) -> None:
        registry = json.loads(json.dumps(self.registry))
        registry["discovery"]["maxMarkets"] = 6
        ranked = [
            record("macro-1", "monetary-policy", "macro-1", 1),
            record("energy-1", "energy-commodities", "energy-1", 2),
        ]
        selected = hardened.balanced_selection(ranked, registry)
        self.assertEqual({item["id"] for item in selected}, {"macro-1", "energy-1"})


if __name__ == "__main__":
    unittest.main()
