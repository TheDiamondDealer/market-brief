"""Unit tests for the PR-2 news-impact tagger pipeline.

Covers the pure validator (enum/vocabulary drops), the ledger merge / prune /
retry-cap state machine, and the tagger driven by an injected FAKE caller so no
test ever touches the network.
"""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import tag_impacts as tagger  # noqa: E402
import validate_impact_tags as validator  # noqa: E402

NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)
VALID_IDS = {"gold", "wti", "us10y", "dxy", "spx"}


def _item(item_id: str, *, seen_at: str = "2026-07-24T06:00:00Z") -> dict:
    return {
        "id": item_id,
        "source": "gdelt",
        "headline": f"Headline {item_id}",
        "url": f"https://example.com/{item_id}",
        "domain": "example.com",
        "seenAt": seen_at,
        "topic": "Energy & security",
    }


def _empty_ledger() -> dict:
    return {
        "schemaVersion": 1,
        "generatedAtUtc": "2026-07-24T00:00:00Z",
        "model": "claude-haiku-4-5",
        "items": [],
    }


def _good_tag(asset_id: str = "gold") -> dict:
    return {
        "assetId": asset_id,
        "direction": "up",
        "confidence": "medium",
        "mechanism": "Sanctions tighten supply, lifting the price.",
    }


def _caller_returning(payload) -> object:
    text = payload if isinstance(payload, str) else json.dumps(payload)

    def _caller(prompt: str) -> str:  # noqa: ARG001
        return text

    return _caller


def _caller_raising(exc: Exception) -> object:
    def _caller(prompt: str) -> str:  # noqa: ARG001
        raise exc

    return _caller


# --------------------------------------------------------------------------- #
# Validator (pure functions)
# --------------------------------------------------------------------------- #
class ValidatorTests(unittest.TestCase):
    def test_valid_asset_ids_from_registry(self) -> None:
        registry = {"assets": [{"id": "gold", "label": "Gold"}, {"id": "wti", "label": "WTI"}]}
        self.assertEqual(validator.valid_asset_ids(registry), {"gold", "wti"})

    def test_validate_tag_accepts_well_formed(self) -> None:
        self.assertTrue(validator.validate_tag(_good_tag("gold"), VALID_IDS))

    def test_validate_tag_drops_unknown_asset(self) -> None:
        self.assertFalse(validator.validate_tag(_good_tag("dogecoin"), VALID_IDS))

    def test_validate_tag_drops_bad_direction(self) -> None:
        bad = _good_tag()
        bad["direction"] = "sideways"
        self.assertFalse(validator.validate_tag(bad, VALID_IDS))

    def test_validate_tag_drops_bad_confidence(self) -> None:
        bad = _good_tag()
        bad["confidence"] = "certain"
        self.assertFalse(validator.validate_tag(bad, VALID_IDS))

    def test_validate_tag_drops_blank_mechanism(self) -> None:
        bad = _good_tag()
        bad["mechanism"] = "   "
        self.assertFalse(validator.validate_tag(bad, VALID_IDS))

    def test_validate_tag_drops_non_dict(self) -> None:
        self.assertFalse(validator.validate_tag("nope", VALID_IDS))

    def test_validate_item_output_filters_invalid_keeps_valid(self) -> None:
        raw = {"itemId": "x", "tags": [_good_tag("gold"), _good_tag("dogecoin")]}
        out = validator.validate_item_output(raw, VALID_IDS)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["assetId"], "gold")

    def test_validate_item_output_empty_tags_is_valid(self) -> None:
        out = validator.validate_item_output({"itemId": "x", "tags": []}, VALID_IDS)
        self.assertEqual(out, [])

    def test_validate_item_output_malformed_returns_none(self) -> None:
        self.assertIsNone(validator.validate_item_output("not-a-dict", VALID_IDS))
        self.assertIsNone(validator.validate_item_output({"itemId": "x"}, VALID_IDS))
        self.assertIsNone(validator.validate_item_output({"tags": "nope"}, VALID_IDS))

    def test_validate_item_output_returns_clean_tag_shape(self) -> None:
        raw = {"itemId": "x", "tags": [dict(_good_tag("gold"), extra="junk")]}
        out = validator.validate_item_output(raw, VALID_IDS)
        self.assertEqual(set(out[0].keys()), {"assetId", "direction", "confidence", "mechanism"})


# --------------------------------------------------------------------------- #
# Ledger prune / select
# --------------------------------------------------------------------------- #
class LedgerHousekeepingTests(unittest.TestCase):
    def test_prune_drops_items_older_than_seven_days(self) -> None:
        ledger = _empty_ledger()
        old = _item("old", seen_at="2026-07-10T00:00:00Z")   # 14 days
        fresh = _item("fresh", seen_at="2026-07-23T00:00:00Z")  # 1 day
        ledger["items"] = [old, fresh]
        tagger.prune_ledger(ledger, NOW)
        self.assertEqual([i["id"] for i in ledger["items"]], ["fresh"])

    def test_prune_keeps_unparseable_dates(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [_item("weird", seen_at="never")]
        tagger.prune_ledger(ledger, NOW)
        self.assertEqual([i["id"] for i in ledger["items"]], ["weird"])

    def test_select_pending_excludes_tagged_and_unavailable(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [
            {**_item("done"), "tagState": "tagged", "attempts": 0, "taggedAtUtc": "x", "tags": []},
            {**_item("dead"), "tagState": "unavailable", "attempts": 3, "taggedAtUtc": None, "tags": []},
            {**_item("retry"), "tagState": "tagFailed", "attempts": 1, "taggedAtUtc": None, "tags": []},
        ]
        inputs = [_item("done"), _item("dead"), _item("retry"), _item("brand-new")]
        pending = tagger.select_pending(ledger, inputs)
        self.assertEqual({i["id"] for i in pending}, {"retry", "brand-new"})

    def test_select_pending_excludes_tagfailed_at_cap(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [
            {**_item("capped"), "tagState": "tagFailed", "attempts": 3, "taggedAtUtc": None, "tags": []},
        ]
        pending = tagger.select_pending(ledger, [_item("capped")])
        self.assertEqual(pending, [])


# --------------------------------------------------------------------------- #
# Tagger state machine (injected fake caller)
# --------------------------------------------------------------------------- #
class TaggerTests(unittest.TestCase):
    def test_good_output_marks_tagged_with_validated_tags(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": [_good_tag("gold"), _good_tag("bogus")]}]
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagged")
        self.assertEqual([t["assetId"] for t in entry["tags"]], ["gold"])
        self.assertEqual(entry["attempts"], 0)
        self.assertTrue(entry["taggedAtUtc"].endswith("Z"))

    def test_empty_tags_is_a_valid_tagged_answer(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": []}]
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagged")
        self.assertEqual(entry["tags"], [])

    def test_malformed_item_marks_tagfailed_and_increments_attempts(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "a", "tags": "not-a-list"}]
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagFailed")
        self.assertEqual(entry["attempts"], 1)
        self.assertIsNone(entry["taggedAtUtc"])

    def test_missing_itemid_in_output_marks_tagfailed(self) -> None:
        ledger = _empty_ledger()
        payload = [{"itemId": "somebody-else", "tags": []}]
        tagger.tag_pending(ledger, [_item("a")], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagFailed")
        self.assertEqual(entry["attempts"], 1)

    def test_unparseable_batch_marks_all_pending_tagfailed(self) -> None:
        ledger = _empty_ledger()
        tagger.tag_pending(
            ledger, [_item("a"), _item("b")], caller=_caller_returning("this is not json"), now=NOW
        )
        self.assertEqual({i["tagState"] for i in ledger["items"]}, {"tagFailed"})
        self.assertTrue(all(i["attempts"] == 1 for i in ledger["items"]))

    def test_retry_of_tagfailed_can_succeed(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [
            {**_item("a"), "tagState": "tagFailed", "attempts": 1, "taggedAtUtc": None, "tags": []},
        ]
        payload = [{"itemId": "a", "tags": [_good_tag("gold")]}]
        tagger.tag_pending(ledger, [ledger["items"][0]], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["tagState"], "tagged")
        self.assertEqual(entry["attempts"], 1)  # failed-attempt count preserved
        self.assertEqual(len(entry["tags"]), 1)

    def test_third_failure_caps_to_unavailable(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [
            {**_item("a"), "tagState": "tagFailed", "attempts": 2, "taggedAtUtc": None, "tags": []},
        ]
        payload = [{"itemId": "a", "tags": "garbage"}]
        tagger.tag_pending(ledger, [ledger["items"][0]], caller=_caller_returning(payload), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["attempts"], 3)
        self.assertEqual(entry["tagState"], "unavailable")

    def test_tagged_item_is_never_retagged(self) -> None:
        ledger = _empty_ledger()
        original = {**_item("a"), "tagState": "tagged", "attempts": 0,
                    "taggedAtUtc": "2026-07-20T00:00:00Z", "tags": [_good_tag("gold")]}
        ledger["items"] = [original]
        pending = tagger.select_pending(ledger, [_item("a")])
        self.assertEqual(pending, [])
        # even if forced through, an empty pending list is a no-op
        tagger.tag_pending(ledger, pending, caller=_caller_raising(RuntimeError("boom")), now=NOW)
        self.assertEqual(ledger["items"][0], original)

    def test_fail_open_when_caller_raises_leaves_items_untouched(self) -> None:
        ledger = _empty_ledger()
        tagger.tag_pending(
            ledger, [_item("a"), _item("b")], caller=_caller_raising(RuntimeError("no key")), now=NOW
        )
        # whole-batch outage: nothing added, no attempts burned
        self.assertEqual(ledger["items"], [])

    def test_fail_open_does_not_increment_attempts_on_existing_tagfailed(self) -> None:
        ledger = _empty_ledger()
        ledger["items"] = [
            {**_item("a"), "tagState": "tagFailed", "attempts": 1, "taggedAtUtc": None, "tags": []},
        ]
        tagger.tag_pending(ledger, [ledger["items"][0]], caller=_caller_raising(OSError("timeout")), now=NOW)
        entry = ledger["items"][0]
        self.assertEqual(entry["attempts"], 1)
        self.assertEqual(entry["tagState"], "tagFailed")


# --------------------------------------------------------------------------- #
# Input normalization
# --------------------------------------------------------------------------- #
class NormalizeTests(unittest.TestCase):
    def test_normalize_gdelt_shape(self) -> None:
        data = {"articles": [{
            "id": "g1", "title": "Oil spikes", "url": "https://x/1", "domain": "x.com",
            "seenAt": "2026-07-24T06:00:00Z", "topicIds": ["energy"], "topics": ["Energy & security"],
        }]}
        rows = tagger.normalize_gdelt(data)
        self.assertEqual(rows[0], {
            "id": "g1", "source": "gdelt", "headline": "Oil spikes", "url": "https://x/1",
            "domain": "x.com", "seenAt": "2026-07-24T06:00:00Z", "topic": "Energy & security",
        })

    def test_normalize_conflict_shape(self) -> None:
        data = {"items": [{
            "id": "c1", "title": "Strikes hit port", "summary": "s", "url": "https://y/1",
            "publishedAt": "2026-07-23T14:22:00+00:00",
            "source": {"id": "us-war", "name": "US War News"}, "tags": ["Iran"],
        }]}
        rows = tagger.normalize_conflict(data)
        self.assertEqual(rows[0]["id"], "c1")
        self.assertEqual(rows[0]["source"], "conflict-watch")
        self.assertEqual(rows[0]["headline"], "Strikes hit port")
        self.assertEqual(rows[0]["seenAt"], "2026-07-23T14:22:00+00:00")
        self.assertEqual(rows[0]["topic"], "US War News")
        self.assertEqual(rows[0]["domain"], "US War News")


if __name__ == "__main__":
    unittest.main()
