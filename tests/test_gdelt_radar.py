from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


update = load_module("update_gdelt_radar", ROOT / "scripts" / "update_gdelt_radar.py")
validator = load_module("validate_gdelt_radar", ROOT / "scripts" / "validate_gdelt_radar.py")


class GdeltRadarTests(unittest.TestCase):
    def test_canonical_url_removes_tracking(self):
        self.assertEqual(
            update.canonical_url("https://Example.com/story?utm_source=x&id=7#part"),
            "https://example.com/story?id=7",
        )

    def test_duplicate_article_merges_topics(self):
        left = {"topicIds": ["macro-policy"], "topics": ["Macro"], "assets": ["rates"], "materialityScore": 12, "duplicateCount": 1, "seenAt": "2026-07-16T00:00:00Z"}
        right = {"topicIds": ["energy-security"], "topics": ["Energy"], "assets": ["brent"], "materialityScore": 20, "duplicateCount": 1, "seenAt": "2026-07-16T01:00:00Z"}
        merged = update.merge_article(left, right)
        self.assertEqual(merged["topicIds"], ["energy-security", "macro-policy"])
        self.assertEqual(merged["duplicateCount"], 2)
        self.assertEqual(merged["materialityScore"], 20)
        self.assertEqual(merged["seenAt"], "2026-07-16T01:00:00Z")

    def test_total_failure_retains_previous_snapshot_as_stale(self):
        previous = {
            "collection": {"lastSuccessfulAt": "2026-07-15T00:00:00Z"},
            "articles": [{
                "id": "old", "title": "A sufficiently long retained headline", "url": "https://example.com/a",
                "domain": "example.com", "language": "English", "sourceCountry": "US", "seenAt": "2026-07-15T00:00:00Z",
                "firstSeenAt": "2026-07-15T00:00:00Z", "topicIds": ["macro-policy"], "topics": ["Macro"],
                "assets": ["rates"], "materialityScore": 25, "sourceTier": "discovery", "verificationStatus": "unverified",
                "verificationNote": "Confirm against an official source.", "duplicateCount": 1,
            }],
        }
        with patch.object(update, "request_json", side_effect=OSError("offline")):
            payload = update.collect(previous)
        self.assertEqual(payload["collection"]["status"], "stale")
        self.assertEqual(payload["articles"][0]["id"], "old")

    def test_validator_rejects_article_body(self):
        payload = {
            "schemaVersion": 1,
            "provider": {"id": "gdelt-doc-2", "readOnly": True},
            "collection": {"status": "current", "selectedArticleCount": 1},
            "articles": [{
                "id": "1", "title": "This is a valid headline with enough characters", "url": "https://example.com/story",
                "sourceTier": "discovery", "verificationStatus": "unverified", "materialityScore": 10,
                "topicIds": [], "topics": [], "assets": [], "body": "not permitted",
            }],
            "sourceStatus": [{"status": "current"}],
            "methodology": {"verification": "Confirm with an official source"},
        }
        with self.assertRaises(ValueError):
            validator.validate(payload)

    def test_seed_payload_validates(self):
        payload = json.loads((ROOT / "site" / "data" / "gdelt-radar.json").read_text(encoding="utf-8"))
        validator.validate(payload)


if __name__ == "__main__":
    unittest.main()
