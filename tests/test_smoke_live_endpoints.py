"""Offline unit tests for the live-endpoint smoke — the shape validators and the
retry/verdict logic are pure and injectable, so no test touches the network."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import smoke_live_endpoints as smoke  # noqa: E402


class ShapeValidatorTests(unittest.TestCase):
    def test_asx_accepts_markit_shape(self) -> None:
        self.assertIsNone(smoke.validate_asx(b'{"data":{"symbol":"BHP","items":[{"headline":"x"}]}}'))

    def test_asx_rejects_missing_items_or_junk(self) -> None:
        self.assertIsNotNone(smoke.validate_asx(b'{"data":{"symbol":"BHP"}}'))   # no items
        self.assertIsNotNone(smoke.validate_asx(b'{"error_code":"uri-not-found"}'))  # the retired-API body
        self.assertIsNotNone(smoke.validate_asx(b"<html>404</html>"))

    def test_rba_accepts_feed_with_items(self) -> None:
        self.assertIsNone(smoke.validate_rba(b"<rdf><item><title>Statement</title></item></rdf>"))

    def test_rba_rejects_empty_or_non_xml(self) -> None:
        self.assertIsNotNone(smoke.validate_rba(b"<rdf></rdf>"))
        self.assertIsNotNone(smoke.validate_rba(b"not xml <"))

    def test_usda_accepts_results(self) -> None:
        self.assertIsNone(smoke.validate_usda(b'{"results":[{"id":"1","title":"WASDE"}]}'))

    def test_usda_rejects_empty_results(self) -> None:
        self.assertIsNotNone(smoke.validate_usda(b'{"results":[]}'))
        self.assertIsNotNone(smoke.validate_usda(b"{}"))


class RunCheckTests(unittest.TestCase):
    def test_healthy_endpoint_returns_none(self) -> None:
        check = {"id": "x", "url": "https://x", "validate": lambda body: None}
        self.assertIsNone(smoke.run_check(check, lambda url: b"ok"))

    def test_bad_shape_fails_without_retry(self) -> None:
        calls = {"n": 0}

        def fetcher(url: str) -> bytes:
            calls["n"] += 1
            return b"bad"

        check = {"id": "x", "url": "https://x", "validate": lambda body: "shape changed"}
        self.assertEqual(smoke.run_check(check, fetcher), "shape changed")
        self.assertEqual(calls["n"], 1)  # deterministic shape error is not retried

    def test_persistent_transport_error_reports_unreachable(self) -> None:
        calls = {"n": 0}

        def fetcher(url: str) -> bytes:
            calls["n"] += 1
            raise OSError("connection refused")

        check = {"id": "x", "url": "https://x", "validate": lambda body: None}
        result = smoke.run_check(check, fetcher, attempts=3)
        self.assertIn("unreachable", result)
        self.assertEqual(calls["n"], 3)


if __name__ == "__main__":
    unittest.main()
