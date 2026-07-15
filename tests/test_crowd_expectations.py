from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_crowd_expectations as crowd  # noqa: E402
import update_crowd_expectations_hardened as hardened  # noqa: E402,F401


def sample_market(**overrides):
    row = {
        "id": "123",
        "question": "Will the Federal Reserve cut interest rates by September?",
        "slug": "fed-cut-by-september",
        "description": (
            "This market resolves Yes if the Federal Reserve lowers its target range "
            "by the stated date. The resolution source is the official Federal Reserve announcement."
        ),
        "resolutionSource": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.60", "0.40"]',
        "bestBid": 0.59,
        "bestAsk": 0.61,
        "spread": 0.02,
        "lastTradePrice": 0.605,
        "liquidityNum": 150000,
        "volume24hr": 250000,
        "volumeNum": 1000000,
        "oneDayPriceChange": 0.08,
        "oneWeekPriceChange": 0.12,
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "restricted": True,
        "endDate": "2026-09-30T00:00:00Z",
        "updatedAt": "2026-07-15T01:00:00Z",
        "events": [{
            "slug": "fed-cut-by-september",
            "title": "Federal Reserve policy",
            "openInterest": 200000,
        }],
    }
    row.update(overrides)
    return row


class CrowdCollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(
            (ROOT / "scripts" / "crowd_expectations_registry.json").read_text(encoding="utf-8")
        )

    def test_binary_yes_probability_parses_string_arrays(self):
        probability, index = crowd.binary_yes_probability(sample_market())
        self.assertEqual(index, 0)
        self.assertEqual(probability, 0.60)

    def test_non_binary_market_is_rejected(self):
        probability, index = crowd.binary_yes_probability(sample_market(outcomes='["A", "B"]'))
        self.assertIsNone(probability)
        self.assertIsNone(index)

    def test_market_with_yes_no_and_third_outcome_is_rejected(self):
        probability, index = crowd.binary_yes_probability(
            sample_market(
                outcomes='["Yes", "No", "Other"]',
                outcomePrices='["0.40", "0.40", "0.20"]',
            )
        )
        self.assertIsNone(probability)
        self.assertIsNone(index)

    def test_sports_market_is_excluded(self):
        category, score = crowd.classify_market(
            sample_market(
                question="Will France win the World Cup?",
                sportsMarketType="soccer_moneyline",
            ),
            self.registry,
        )
        self.assertIsNone(category)
        self.assertEqual(score, 0)

    def test_macro_market_is_classified_and_asset_mapped(self):
        category, score = crowd.classify_market(sample_market(), self.registry)
        self.assertEqual(category["id"], "monetary-policy")
        self.assertGreaterEqual(score, 2)
        assets = crowd.asset_map(category, sample_market())
        self.assertIn("rates", assets)
        self.assertIn("gold", assets)

    def test_foreign_presidential_elections_are_not_us_policy(self):
        for question in (
            "Will Eduardo Bolsonaro win the Brazilian presidential election?",
            "Will a French presidential election be called this year?",
        ):
            with self.subTest(question=question):
                category, score = crowd.classify_market(
                    sample_market(
                        question=question,
                        description="An election market resolved from the national election authority.",
                        events=[{"slug": "foreign-election", "title": question}],
                    ),
                    self.registry,
                )
                self.assertIsNone(category)
                self.assertEqual(score, 0)

    def test_us_presidential_election_requires_us_context(self):
        category, score = crowd.classify_market(
            sample_market(
                question="Who will win the United States presidential election?",
                description="The market resolves from the certified United States result.",
                events=[{"slug": "us-election", "title": "United States presidential election"}],
            ),
            self.registry,
        )
        self.assertEqual(category["id"], "us-policy-elections")
        self.assertGreaterEqual(score, 2)

    def test_provider_intelligence_prose_is_not_intel_company_match(self):
        category, score = crowd.classify_market(
            sample_market(
                question="Will a Satoshi-era wallet move coins this month?",
                description="The event will be monitored using the Arkham Intel Explorer.",
                events=[{"slug": "satoshi-wallet", "title": "Satoshi wallet activity"}],
            ),
            self.registry,
        )
        self.assertIsNone(category)
        self.assertEqual(score, 0)

    def test_celebrity_nomination_market_is_excluded(self):
        category, score = crowd.classify_market(
            sample_market(
                question="Will LeBron James win the 2028 Democratic presidential nomination?",
                description="This market resolves from official Democratic Party sources.",
                events=[{"slug": "nominee", "title": "Democratic Presidential Nominee 2028"}],
            ),
            self.registry,
        )
        self.assertIsNone(category)
        self.assertEqual(score, 0)

    def test_geopolitical_event_outranks_incidental_president_prose(self):
        category, score = crowd.classify_market(
            sample_market(
                question="Will Iran reopen its airspace by July 31?",
                description="President Trump may comment on the event.",
                events=[{"slug": "iran-airspace", "title": "Iran airspace closure"}],
            ),
            self.registry,
        )
        self.assertEqual(category["id"], "geopolitics-security")
        self.assertGreaterEqual(score, 3)

    def test_wti_market_is_not_mapped_to_unrelated_commodities(self):
        category = next(
            item for item in self.registry["categories"] if item["id"] == "energy-commodities"
        )
        market = sample_market(
            question="Will WTI Crude Oil hit $85 in July?",
            description="This market resolves from the active WTI futures contract.",
        )
        assets = crowd.asset_map(category, market)
        self.assertEqual(assets, ["wti"])

    def test_midpoint_is_preferred_when_actual_spread_is_acceptable(self):
        probability, source = crowd.selected_probability(sample_market(), 0.60)
        self.assertEqual(probability, 0.60)
        self.assertEqual(source, "bid-ask midpoint")

    def test_last_trade_is_used_when_actual_book_is_wide(self):
        probability, source = crowd.selected_probability(
            sample_market(bestBid=0.10, bestAsk=0.90, spread=0.01),
            0.60,
        )
        self.assertEqual(probability, 0.605)
        self.assertEqual(source, "last trade")

    def test_history_replaces_same_day_and_retains_unique_dates(self):
        previous = {
            "history": [{
                "date": "2026-07-14",
                "observedAt": "2026-07-14T00:00:00Z",
                "probability": 0.5,
            }]
        }
        first = crowd.day_snapshot(previous, "2026-07-15T00:00:00Z", 0.6)
        second = crowd.day_snapshot({"history": first}, "2026-07-15T06:00:00Z", 0.62)
        self.assertEqual(len(second), 2)
        self.assertEqual(second[-1]["probability"], 0.62)

    def test_resolution_source_is_extracted_from_market_rules(self):
        market = sample_market(
            resolutionSource="",
            description=(
                "The resolution source for this market is the official statement at "
                "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm. "
                "This market resolves after publication."
            ),
        )
        self.assertEqual(
            hardened.resolution_source(market),
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        )
        category, score = crowd.classify_market(market, self.registry)
        record = hardened.market_record(
            market,
            category,
            score,
            None,
            "2026-07-15T01:00:00Z",
            90,
        )
        self.assertEqual(record["resolutionSource"], hardened.resolution_source(market))
        self.assertIn("Resolution source supplied", record["qualityReasons"])

    def test_missing_resolution_source_caps_grade_below_a(self):
        market = sample_market(
            resolutionSource="",
            description="A clearly worded active market without a stated resolution source or URL.",
            events=[{"slug": "test", "title": "Test", "openInterest": 200000}],
        )
        score, grade, reasons = hardened.quality_score(market, 4)
        self.assertLessEqual(score, 79)
        self.assertEqual(grade, "B")
        self.assertTrue(any("capped" in reason.lower() for reason in reasons))

    def test_legitimate_signature_word_in_market_rules_is_allowed(self):
        market = sample_market(
            description=(
                "This market resolves after the President's signature appears on the enacted bill. "
                "The resolution source is https://www.congress.gov/."
            )
        )
        with patch.object(crowd, "discover_markets", return_value=[market]):
            result = crowd.build_dataset(self.registry, {})
        self.assertEqual(result["collection"]["status"], "current")
        hardened.validate_output(result)

    def test_build_dataset_creates_read_only_shock(self):
        with patch.object(crowd, "discover_markets", return_value=[sample_market()]):
            result = crowd.build_dataset(self.registry, {})
        self.assertEqual(result["collection"]["status"], "current")
        self.assertEqual(len(result["markets"]), 1)
        self.assertTrue(result["markets"][0]["readOnly"])
        self.assertEqual(len(result["shocks"]), 1)

    def test_source_failure_retains_previous_market_as_stale(self):
        previous = {
            "collection": {"lastSuccessfulAt": "2026-07-14T00:00:00Z"},
            "markets": [{
                "id": "old",
                "readOnly": True,
                "status": "current",
                "category": "Monetary Policy & Macro",
                "categoryId": "monetary-policy",
                "question": "Old verified market",
                "probability": 0.5,
                "probabilityPercent": 50.0,
                "probabilitySource": "last trade",
                "change24hPoints": None,
                "change7dPoints": None,
                "bestBid": None,
                "bestAsk": None,
                "spread": None,
                "liquidity": 10000,
                "volume24h": 1000,
                "volumeTotal": 10000,
                "openInterest": 0,
                "qualityScore": 60,
                "qualityGrade": "C",
                "qualityReasons": ["retained"],
                "relevanceScore": 1,
                "assets": ["rates"],
                "resolutionSource": None,
                "description": "",
                "endDate": None,
                "updatedAt": "2026-07-14T00:00:00Z",
                "collectedAt": "2026-07-14T00:00:00Z",
                "sourceUrl": "https://polymarket.com/",
                "restricted": True,
                "acceptingOrders": True,
                "history": [],
                "slug": None,
                "eventTitle": None,
            }],
        }
        with patch.object(crowd, "discover_markets", side_effect=RuntimeError("temporary outage")):
            result = crowd.build_dataset(self.registry, previous)
        self.assertEqual(result["collection"]["status"], "partial")
        self.assertEqual(result["markets"][0]["status"], "stale")

    def test_committed_seed_validates(self):
        subprocess.run(
            ["python", "scripts/validate_crowd_expectations.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


class CrowdIntegrationTests(unittest.TestCase):
    def test_feature_manifest_loads_crowd_assets(self):
        text = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertIn("route: 'crowd-expectations'", text)
        for path in (
            "features/crowd-expectations/crowd-data.js",
            "features/crowd-expectations/crowd-health.js",
            "features/crowd-expectations/crowd-page.js",
            "features/crowd-expectations/crowd-command.js",
            "features/crowd-expectations/crowd-asset.js",
        ):
            self.assertIn(path, text)

    def test_source_health_extension_is_idempotent(self):
        text = (
            ROOT / "site" / "features" / "crowd-expectations" / "crowd-health.js"
        ).read_text(encoding="utf-8")
        self.assertIn("alreadyInjected", text)
        self.assertIn("if (alreadyInjected(base, expected)) return", text)

    def test_workflow_is_read_only_and_scheduled(self):
        workflow = (
            ROOT / ".github" / "workflows" / "update-crowd-expectations.yml"
        ).read_text(encoding="utf-8").lower()
        self.assertIn("python scripts/update_crowd_expectations_hardened.py", workflow)
        self.assertIn("python scripts/validate_crowd_expectations.py", workflow)
        self.assertIn("cron:", workflow)
        for prohibited in ("private_key", "walletconnect", "post_order", "create_order"):
            self.assertNotIn(prohibited, workflow)

    def test_collector_has_no_order_endpoint_or_secret_contract(self):
        collector = (
            (ROOT / "scripts" / "update_crowd_expectations.py").read_text(encoding="utf-8")
            + (ROOT / "scripts" / "update_crowd_expectations_hardened.py").read_text(encoding="utf-8")
        ).lower()
        registry = (
            ROOT / "scripts" / "crowd_expectations_registry.json"
        ).read_text(encoding="utf-8")
        self.assertIn("gamma-api.polymarket.com/markets", registry)
        self.assertNotRegex(collector, r"https?://[^\"']+/(order|orders)(?:[/?#]|[\"'])")
        self.assertNotRegex(collector, r"os\.environ\.get\([\"'](?:private_key|api_secret)")
        self.assertNotRegex(collector, r"(?:post|put)\s*=\s*true")


if __name__ == "__main__":
    unittest.main()
