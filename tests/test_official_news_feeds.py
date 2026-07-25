from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_official_news as news  # noqa: E402


class OfficialNewsCollectorTests(unittest.TestCase):
    def test_asx_collector_accepts_official_metadata_and_fallback_url(self) -> None:
        config = {
            "sourcePage": "https://www.asx.com.au/markets/trade-our-cash-market/announcements",
            "endpointTemplate": "https://www.asx.com.au/asx/1/company/{ticker}/announcements?count={count}&market_sensitive=false",
            "countPerTicker": 5,
            "maxRecords": 10,
            "lookbackDays": 3650,
            "tickers": ["LYC"],
        }
        payload = {
            "data": [{
                "id": "02999999",
                "issuer_code": "LYC",
                "issuer_short_name": "Lynas Rare Earths",
                "header": "Quarterly Activities Report",
                "document_release_date": "2026-07-15T23:30:00+10:00",
                "market_sensitive": True,
                "announcement_type_description": "Periodic Reports",
                "number_of_pages": 18,
            }]
        }
        with patch.object(news, "request_json", return_value=payload), patch.object(news.time, "sleep"):
            result = news.collect_asx(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "current")
        self.assertEqual(result["records"][0]["ticker"], "LYC")
        self.assertTrue(result["records"][0]["marketSensitive"])
        self.assertEqual(result["records"][0]["observedAt"], "2026-07-15T13:30:00Z")
        self.assertEqual(
            result["records"][0]["sourceUrl"],
            "https://www.asx.com.au/asx/1/file/02999999/announcement",
        )

    def test_asx_identity_mismatch_is_rejected(self) -> None:
        config = {
            "sourcePage": "https://www.asx.com.au/markets/trade-our-cash-market/announcements",
            "endpointTemplate": "https://www.asx.com.au/asx/1/company/{ticker}/announcements?count={count}&market_sensitive=false",
            "countPerTicker": 5,
            "maxRecords": 10,
            "lookbackDays": 3650,
            "tickers": ["LYC"],
        }
        payload = {"data": [{"id": "1", "issuer_code": "BHP", "header": "Wrong issuer"}]}
        with patch.object(news, "request_json", return_value=payload), patch.object(news.time, "sleep"):
            result = news.collect_asx(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["records"], [])
        self.assertIn("issuer mismatch", result["error"])

    def test_fed_rss_parser_keeps_official_links_only(self) -> None:
        payload = b"""<?xml version='1.0'?><rss><channel>
        <item><title>Federal Reserve issues FOMC statement</title>
        <link>https://www.federalreserve.gov/newsevents/pressreleases/monetary20260715a.htm</link>
        <guid>statement-1</guid><pubDate>Wed, 15 Jul 2026 18:00:00 GMT</pubDate></item>
        <item><title>Untrusted mirror</title><link>https://example.com/mirror</link><guid>mirror</guid></item>
        </channel></rss>"""
        records = news.parse_feed(payload, {"name": "Monetary policy releases", "group": "Monetary Policy", "maxItems": 10})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["observedAt"], "2026-07-15T18:00:00Z")
        self.assertEqual(records[0]["kind"], "policy-release")

    def test_fed_collector_deduplicates_overlapping_feeds(self) -> None:
        config = {
            "sourcePage": "https://www.federalreserve.gov/feeds/feeds.htm",
            "lookbackDays": 3650,
            "maxRecords": 10,
            "feeds": [
                {"id": "one", "name": "One", "group": "Policy", "url": "https://www.federalreserve.gov/feeds/one.xml", "maxItems": 10},
                {"id": "two", "name": "Two", "group": "Policy", "url": "https://www.federalreserve.gov/feeds/two.xml", "maxItems": 10},
            ],
        }
        payload = b"""<rss><channel><item><title>Policy release</title>
        <link>https://www.federalreserve.gov/newsevents/pressreleases/test.htm</link>
        <guid>same</guid><pubDate>Wed, 15 Jul 2026 18:00:00 GMT</pubDate></item></channel></rss>"""
        with patch.object(news, "request_bytes", return_value=payload):
            result = news.collect_fed(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 1)

    def test_failed_refresh_retains_previous_news_records_as_stale(self) -> None:
        previous = {
            "sources": [{
                "id": "asx-announcements",
                "records": [{"id": "asx-old", "kind": "announcement", "name": "Old", "sourceUrl": "https://www.asx.com.au/old"}],
                "observedAt": "2026-07-14T00:00:00Z",
                "collectedAt": "2026-07-14T01:00:00Z",
                "lastSuccessfulAt": "2026-07-14T01:00:00Z",
            }]
        }
        config = {
            "sourcePage": "https://www.asx.com.au/markets/trade-our-cash-market/announcements",
            "endpointTemplate": "https://www.asx.com.au/asx/1/company/{ticker}/announcements?count={count}&market_sensitive=false",
            "countPerTicker": 5,
            "maxRecords": 10,
            "lookbackDays": 45,
            "tickers": ["LYC"],
        }
        with patch.object(news, "request_json", side_effect=OSError("temporary outage")), patch.object(news.time, "sleep"):
            result = news.collect_asx(config, previous, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["records"][0]["id"], "asx-old")


class RbaAndUsdaCollectorTests(unittest.TestCase):
    def test_news_source_id_set_includes_rba_and_usda(self) -> None:
        self.assertEqual(
            news.NEWS_SOURCE_IDS,
            {"asx-announcements", "federal-reserve-policy", "rba-media-releases", "usda-wasde"},
        )

    def test_rba_rdf_parser_keeps_official_releases_only(self) -> None:
        # RBA publishes an RSS 1.0 / RDF feed: items are rdf:about with <dc:date>, not <pubDate>.
        payload = b"""<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns="http://purl.org/rss/1.0/">
          <item rdf:about="https://www.rba.gov.au/media-releases/2026/mr-26-15.html">
            <title>Statement by the Reserve Bank Board: Monetary Policy Decision</title>
            <link>https://www.rba.gov.au/media-releases/2026/mr-26-15.html</link>
            <dc:date>2026-07-08T05:30:00+00:00</dc:date>
            <description>Cash rate decision</description>
          </item>
          <item rdf:about="https://example.com/mirror">
            <title>Untrusted mirror of an RBA release</title>
            <link>https://example.com/mirror</link>
            <dc:date>2026-07-08T00:00:00+00:00</dc:date>
          </item>
        </rdf:RDF>"""
        config = {
            "sourcePage": "https://www.rba.gov.au/media-releases/",
            "lookbackDays": 3650, "maxItems": 40, "maxRecords": 40,
            "feeds": [{"id": "media-releases", "name": "Media releases", "group": "Media Releases",
                       "url": "https://www.rba.gov.au/rss/rss-cb-media-releases.xml"}],
        }
        with patch.object(news, "request_bytes", return_value=payload):
            result = news.collect_rba(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 1)  # off-domain mirror rejected
        self.assertEqual(result["records"][0]["kind"], "release")
        self.assertEqual(result["records"][0]["observedAt"], "2026-07-08T05:30:00Z")
        self.assertTrue(result["records"][0]["sourceUrl"].startswith("https://www.rba.gov.au/"))
        self.assertEqual(result["records"][0]["publisher"], "Reserve Bank of Australia")

    def test_rba_failure_retains_previous_records_as_stale(self) -> None:
        previous = {"sources": [{
            "id": "rba-media-releases",
            "records": [{"id": "rba-old", "kind": "release", "name": "Old", "sourceUrl": "https://www.rba.gov.au/old"}],
            "observedAt": "2026-07-01T00:00:00Z", "collectedAt": "2026-07-01T01:00:00Z",
            "lastSuccessfulAt": "2026-07-01T01:00:00Z",
        }]}
        config = {"sourcePage": "https://www.rba.gov.au/media-releases/", "lookbackDays": 180, "maxRecords": 40,
                  "feeds": [{"id": "media-releases", "name": "Media releases", "group": "Media Releases", "url": "https://www.rba.gov.au/rss/x.xml"}]}
        with patch.object(news, "request_bytes", side_effect=OSError("temporary outage")):
            result = news.collect_rba(config, previous, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "stale")
        self.assertEqual(result["records"][0]["id"], "rba-old")

    def test_usda_wasde_builds_release_records(self) -> None:
        payload = {"results": [
            {"id": "795974", "title": "World Agricultural Supply and Demand Estimates",
             "release_datetime": "2026-07-10T12:00:00+0000",
             "files": ["https://esmis.nal.usda.gov/sites/default/release-files/795974/wasde0726.pdf"]},
            {"id": "795937", "title": "World Agricultural Supply and Demand Estimates",
             "release_datetime": "2026-06-11T12:00:00+0000",
             "files": ["https://esmis.nal.usda.gov/sites/default/release-files/795937/wasde0626.pdf"]},
        ]}
        config = {"sourcePage": "https://www.usda.gov/oce/commodity/wasde",
                  "endpoint": "https://usda.library.cornell.edu/api/v1/release/findByIdentifier/wasde",
                  "lookbackDays": 3650, "maxItems": 24, "maxRecords": 12}
        with patch.object(news, "request_json", return_value=payload):
            result = news.collect_usda(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "current")
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["kind"], "release")
        self.assertEqual(result["records"][0]["observedAt"], "2026-07-10T12:00:00Z")
        self.assertTrue(result["records"][0]["sourceUrl"].endswith(".pdf"))
        self.assertEqual(result["records"][0]["publisher"], "USDA World Agricultural Outlook Board")

    def test_usda_lookback_excludes_stale_releases(self) -> None:
        payload = {"results": [{"id": "1", "title": "WASDE", "release_datetime": "2020-01-01T12:00:00+0000",
                                "files": ["https://esmis.nal.usda.gov/old.pdf"]}]}
        config = {"sourcePage": "https://www.usda.gov/oce/commodity/wasde", "endpoint": "https://x",
                  "lookbackDays": 30, "maxItems": 24, "maxRecords": 12}
        with patch.object(news, "request_json", return_value=payload):
            result = news.collect_usda(config, {}, "2026-07-16T00:00:00Z")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["records"], [])


class OfficialNewsIntegrationTests(unittest.TestCase):
    def test_registry_includes_rba_and_usda_blocks(self) -> None:
        registry = json.loads((ROOT / "scripts" / "official_news_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(registry["rba"]["feeds"]), 1)
        self.assertTrue(all(feed["url"].startswith("https://www.rba.gov.au/rss/") for feed in registry["rba"]["feeds"]))
        self.assertTrue(registry["usda"]["endpoint"].startswith("https://usda.library.cornell.edu/"))

    def test_registry_uses_only_official_asx_and_fed_endpoints(self) -> None:
        registry = json.loads((ROOT / "scripts" / "official_news_registry.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(registry["asx"]["tickers"]), 20)
        self.assertTrue(registry["asx"]["endpointTemplate"].startswith("https://www.asx.com.au/"))
        self.assertEqual(len(registry["fed"]["feeds"]), 4)
        self.assertTrue(all(row["url"].startswith("https://www.federalreserve.gov/feeds/") for row in registry["fed"]["feeds"]))

    def test_workflow_preserves_previous_snapshot_before_base_refresh(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-official-feeds.yml").read_text(encoding="utf-8")
        self.assertIn("official-feeds-before.json", workflow)
        self.assertIn("python scripts/update_official_news.py", workflow)
        self.assertIn("python scripts/update_official_feeds_resilient.py", workflow)

    def test_frontend_supports_announcement_and_policy_release_cards(self) -> None:
        page = (ROOT / "site" / "features" / "official-feeds" / "official-feeds-page.js").read_text(encoding="utf-8")
        self.assertIn("record.kind === 'announcement'", page)
        self.assertIn("record.kind === 'policy-release'", page)


if __name__ == "__main__":
    unittest.main()
