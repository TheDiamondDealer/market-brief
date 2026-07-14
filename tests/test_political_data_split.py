from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_political_data_split import RECENT_PER_TRACKER, browser_bootstrap, build_split


class PoliticalDataSplitTests(unittest.TestCase):
    def dataset(self) -> dict:
        trades = []
        for index in range(45):
            year = 2025 if index < 20 else 2026
            trades.append({
                "id": f"trade-{index}",
                "filingId": f"filing-{index // 3}",
                "asset": "Example Corp (EXM)",
                "ticker": "EXM",
                "type": "Purchase" if index % 2 == 0 else "Sale",
                "owner": "SP" if index % 3 else "Self",
                "traded": f"{year}-06-{(index % 28) + 1:02d}",
                "filed": f"{year}-07-{(index % 28) + 1:02d}",
                "lag": "30 days",
                "lagDays": 30,
                "amount": "$1,001 - $15,000",
                "sourceUrl": f"https://official.example/{index}",
            })
        return {
            "generatedAt": "2026-07-14T00:00:00+10:00",
            "generatedAtHuman": "14 July 2026, 00:00 AEST",
            "methodology": "Official records only",
            "sourceStatus": {"house": {"errors": []}},
            "trackers": {
                "example": {
                    "name": "Example Member",
                    "chamber": "House",
                    "status": "Current",
                    "updated": "14 July 2026",
                    "trades": trades,
                    "portfolio": {"status": "PTR-derived", "holdings": []},
                    "sourceStatus": {"errors": []},
                }
            },
        }

    def test_manifest_summary_annual_files_and_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            split = build_split(self.dataset(), root)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
            ticker_index = json.loads((root / "indexes" / "tickers.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["totalTrades"], 45)
            self.assertEqual(manifest["trackers"]["example"]["years"], [2026, 2025])
            self.assertEqual(json.loads((root / "example" / "2026.json").read_text())["tradeCount"], 25)
            self.assertEqual(json.loads((root / "example" / "2025.json").read_text())["tradeCount"], 20)
            self.assertEqual(len(summary["trackers"]["example"]["recentTrades"]), RECENT_PER_TRACKER)
            self.assertEqual(ticker_index["tickers"][0]["ticker"], "EXM")
            self.assertEqual(ticker_index["tickers"][0]["tradeCount"], 45)
            self.assertEqual(split["manifest"]["trackers"]["example"]["summaryUrl"], "data/political/example/summary.json")

    def test_browser_bootstrap_does_not_embed_full_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            split = build_split(self.dataset(), Path(directory))
            bootstrap = browser_bootstrap(split)
            self.assertIn("window.politicalDisclosureManifest", bootstrap)
            self.assertIn('"lazy":true', bootstrap)
            self.assertNotIn("trade-0\"", bootstrap, "oldest full-history rows should remain in annual files")
            self.assertIn("lazySummaryUrl", bootstrap)

    def test_lazy_browser_adapter_is_syntax_valid(self) -> None:
        subprocess.run(
            ["node", "--check", "site/features/political-flow/political-data.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        text = (ROOT / "site" / "features" / "political-flow" / "political-data.js").read_text(encoding="utf-8")
        for marker in ("manifest", "summary", "tracker", "year", "searchPoliticians", "searchTickers"):
            self.assertIn(marker, text)

    def test_workflow_commits_split_directory(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "update-political-disclosures.yml").read_text(encoding="utf-8")
        self.assertIn("scripts/build_political_data_split.py", workflow)
        self.assertIn("git add site/political-data.js site/data/political-disclosures.json site/data/political-disclosures-summary.json site/data/political", workflow)
        self.assertIn("annual_total", workflow)


if __name__ == "__main__":
    unittest.main()
