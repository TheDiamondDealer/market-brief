from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_conflict_watch as watch  # noqa: E402


def rss(*titles: str) -> bytes:
    items = "".join(
        f"<item><title>{title}</title><description>Official source summary.</description>"
        f"<link>https://example.gov/{index}</link><pubDate>Wed, 15 Jul 2026 12:00:00 GMT</pubDate></item>"
        for index, title in enumerate(titles)
    )
    return f"<?xml version='1.0'?><rss><channel>{items}</channel></rss>".encode()


class ConflictWatchTests(unittest.TestCase):
    def test_title_filter_keeps_market_relevant_conflict_and_rejects_generic_defence_news(self) -> None:
        source = watch.SOURCES[0]
        rows = watch.parse_source(
            source,
            rss("Strait of Hormuz attacks disrupt shipping", "Department announces directed energy research awards"),
            now=datetime(2026, 7, 16, tzinfo=timezone.utc),
        )
        self.assertEqual([row["title"] for row in rows], ["Strait of Hormuz attacks disrupt shipping"])
        self.assertIn("Hormuz", rows[0]["tags"])
        self.assertEqual(rows[0]["dataState"], "current")

    def test_partial_failure_retains_only_previous_items_for_the_failed_source(self) -> None:
        previous_item = {
            "id": "0123456789abcdef",
            "title": "Previously verified update",
            "summary": "Summary",
            "publishedAt": "2026-07-14T12:00:00+00:00",
            "url": "https://example.gov/retained",
            "source": {"id": "us-war-news", "name": "U.S. Department of War — News", "pageUrl": "https://www.war.gov/News/"},
            "tags": ["Conflict"],
            "dataState": "current",
        }
        with mock.patch.object(watch, "fetch_xml", side_effect=[
            rss("Iran conflict escalates in Strait of Hormuz"),
            OSError("temporary source failure"),
            rss("Iran missile strikes reported by official source"),
        ]):
            dataset = watch.collect(
                {"items": [previous_item]},
                now=datetime(2026, 7, 16, tzinfo=timezone.utc),
            )
        retained = next(item for item in dataset["items"] if item["id"] == previous_item["id"])
        self.assertEqual(dataset["collection"]["status"], "partial")
        self.assertEqual(dataset["collection"]["failureCount"], 1)
        self.assertEqual(retained["dataState"], "stale-retained")

    def test_committed_dataset_matches_schema_and_browser_data_is_valid_javascript(self) -> None:
        data = json.loads((ROOT / "site" / "data" / "conflict-watch.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "conflict-watch.schema.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(data))
        self.assertEqual(errors, [], "\n".join(error.message for error in errors[:10]))
        subprocess.run(
            ["node", "--check", "site/features/command-centre/conflict-watch-data.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_command_centre_load_order_and_three_hour_workflow_are_declared(self) -> None:
        loader = (ROOT / "site" / "core" / "feature-loader.js").read_text(encoding="utf-8")
        self.assertLess(loader.index("conflict-watch-data.js"), loader.index("command-page.js"))
        workflow = (ROOT / ".github" / "workflows" / "update-conflict-watch.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '17 */3 * * *'", workflow)
        self.assertIn("python scripts/update_conflict_watch.py", workflow)
        freshness = (ROOT / "site" / "core" / "freshness.js").read_text(encoding="utf-8")
        self.assertIn("family: 'official-conflict'", freshness)
        self.assertIn("expectedCadence: 'Every three hours'", freshness)


if __name__ == "__main__":
    unittest.main()
