from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from political_filing_ledger import FilingIdentity, FilingLedger, PARSER_VERSION, content_hash

FIXTURE = ROOT / "tests" / "fixtures" / "political" / "filing-ledger.json"


class PoliticalFilingLedgerTests(unittest.TestCase):
    def identity(self) -> FilingIdentity:
        return FilingIdentity(
            tracker_id="pelosi",
            chamber="House",
            filing_id="20025001",
            filed="2025-06-01",
            report_url="https://disclosures-clerk.house.gov/example.pdf",
            year=2025,
        )

    def test_unchanged_success_is_not_processed_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = FilingLedger(path)
            identity = self.identity()
            ledger.discover(identity)
            ledger.begin(identity)
            digest = content_hash(b"official filing bytes")
            ledger.success(identity, digest=digest, trade_count=4)
            self.assertFalse(ledger.should_process(identity, known_success=True))
            self.assertEqual(ledger.entry(identity)["parserVersion"], PARSER_VERSION)
            self.assertEqual(ledger.entry(identity)["contentHash"], digest)

    def test_parser_version_change_and_failed_state_are_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
            ledger = FilingLedger(path)
            parsed = self.identity()
            partial = FilingIdentity("tim-moore", "House", "20026002", "2026-06-15", "https://disclosures-clerk.house.gov/partial.pdf", 2026)
            failed = FilingIdentity("sheldon-whitehouse", "Senate", "efd-26003", "2026-07-01", "https://efdsearch.senate.gov/search/view/ptr/efd-26003/", 2026)
            self.assertTrue(ledger.should_process(parsed, known_success=True), "old parser versions must reprocess")
            self.assertTrue(ledger.should_process(partial, known_success=True), "partial filings remain retryable")
            self.assertTrue(ledger.should_process(failed, known_success=True), "failed filings remain retryable")

    def test_content_hash_change_is_recorded_after_reprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = FilingLedger(Path(directory) / "ledger.json")
            identity = self.identity()
            ledger.success(identity, digest="a" * 64, trade_count=2)
            ledger.begin(identity)
            ledger.success(identity, digest="b" * 64, trade_count=3)
            entry = ledger.entry(identity)
            self.assertTrue(entry["contentChanged"])
            self.assertEqual(entry["tradeCount"], 3)

    def test_failure_is_visible_and_persisted_with_retry_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            ledger = FilingLedger(path)
            identity = self.identity()
            ledger.begin(identity)
            ledger.failure(identity, "unsupported official PDF layout")
            ledger.write()
            saved = json.loads(path.read_text(encoding="utf-8"))
            entry = saved["filings"][identity.key]
            self.assertEqual(entry["state"], "failed")
            self.assertIn("unsupported", entry["lastError"])
            self.assertTrue(entry["nextRetryAt"])
            self.assertEqual(saved["summary"]["retryable"], 1)
            self.assertEqual(saved["summary"]["retryableFilings"][0]["filingId"], identity.filing_id)

    def test_workflow_runs_ledger_backed_entrypoint_and_commits_ledger(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-political-disclosures.yml").read_text(encoding="utf-8")
        self.assertIn("python scripts/update_political_disclosures_ledger.py", workflow)
        self.assertIn("site/data/political/filing-ledger.json", workflow)
        self.assertIn("scripts/political_filing_ledger.py", workflow)


if __name__ == "__main__":
    unittest.main()
