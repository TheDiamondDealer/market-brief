from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import update_political_disclosures as political  # noqa: E402
import update_political_disclosures_strict as strict  # noqa: E402


class FakeResponse:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.url = url
        self.content = text.encode("utf-8")

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, text: str) -> None:
        self.text = text

    def request(self, method: str, url: str, timeout: int, **kwargs):
        return FakeResponse(self.text, url)


class PoliticalFixtureTests(unittest.TestCase):
    def test_house_index_fixture_discovers_only_ptr_rows(self) -> None:
        text = (FIXTURES / "political" / "house-index.txt").read_text(encoding="utf-8")
        rows = list(csv_rows(text))
        matched = []
        for row in rows:
            filing_type = political.flexible_get(row, "FilingType", "Filing Type")
            if filing_type.upper() not in {"P", "PTR", "PERIODIC TRANSACTION REPORT"}:
                continue
            if political.person_matches(row["First"], row["Last"], political.TRACKERS["pelosi"]):
                matched.append(row["DocID"])
        self.assertEqual(matched, ["10000001"])

    def test_house_extracted_text_fixture_rejects_header_and_accepts_rows(self) -> None:
        text = (FIXTURES / "political" / "house-ptr-extracted.txt").read_text(encoding="utf-8")
        self.assertFalse(strict.valid_asset("Name: Hon. Nancy Pelosi State/District: CA11"))
        matches = list(strict.ROW_PATTERN.finditer(strict.hardened_clean(text)))
        self.assertEqual(len(matches), 2)
        self.assertTrue(strict.valid_amount(matches[0].group("amount")))
        self.assertEqual(political.map_transaction_type(matches[1].group("type")), "Sale (partial)")

    def test_senate_html_fixture_preserves_owner_dates_range_and_source(self) -> None:
        html = (FIXTURES / "political" / "senate-ptr.html").read_text(encoding="utf-8")
        filing = political.Filing(
            tracker_id="sheldon-whitehouse",
            chamber="Senate",
            filing_id="fixture-senate-1",
            filed="2026-07-10",
            report_url="https://efdsearch.senate.gov/search/view/ptr/fixture-senate-1/",
            year=2026,
        )
        trades = political.parse_senate_report(FakeSession(html), filing)
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual(trade["owner"], "Self")
        self.assertEqual(trade["traded"], "2026-06-20")
        self.assertEqual(trade["filed"], "2026-07-10")
        self.assertEqual(trade["lagDays"], 20)
        self.assertEqual(trade["amount"], "$15,001 - $50,000")
        self.assertEqual(trade["ticker"], "XOM")
        self.assertEqual(trade["sourceUrl"], filing.report_url)

    def test_retention_merge_keeps_verified_history_when_incoming_is_empty(self) -> None:
        previous = json.loads(
            (FIXTURES / "political" / "previous-history.json").read_text(encoding="utf-8")
        )
        trades = previous["trackers"]["pelosi"]["trades"]
        merged = political.merge_trades(trades, [])
        self.assertEqual(merged, trades)

    def test_retention_merge_replaces_same_stable_id_without_duplication(self) -> None:
        previous = json.loads(
            (FIXTURES / "political" / "previous-history.json").read_text(encoding="utf-8")
        )["trackers"]["pelosi"]["trades"]
        updated = dict(previous[0], amount="$15,001 - $50,000")
        merged = political.merge_trades(previous, [updated])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["amount"], "$15,001 - $50,000")


def csv_rows(text: str):
    import csv
    import io

    return csv.DictReader(io.StringIO(text), delimiter="\t")


if __name__ == "__main__":
    unittest.main()
