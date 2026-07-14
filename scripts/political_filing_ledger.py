#!/usr/bin/env python3
"""Durable discovery/download/parser ledger for official political filings."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PARSER_VERSION = "political-ptr-v3"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class FilingIdentity:
    tracker_id: str
    chamber: str
    filing_id: str
    filed: str
    report_url: str
    year: int

    @property
    def key(self) -> str:
        return f"{self.chamber.lower()}:{self.tracker_id}:{self.filing_id}"


class FilingLedger:
    """Persist retryable filing state without treating failures as disappearance."""

    def __init__(self, path: Path, *, parser_version: str = PARSER_VERSION) -> None:
        self.path = path
        self.parser_version = parser_version
        self.data: dict[str, Any] = {
            "schemaVersion": 1,
            "parserVersion": parser_version,
            "updatedAt": None,
            "filings": {},
        }
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(loaded, dict) and isinstance(loaded.get("filings"), dict):
            self.data.update(loaded)
            self.data["parserVersion"] = self.parser_version

    def entry(self, identity: FilingIdentity) -> dict[str, Any]:
        filings = self.data.setdefault("filings", {})
        entry = filings.setdefault(identity.key, {})
        entry.update({
            "trackerId": identity.tracker_id,
            "chamber": identity.chamber,
            "filingId": identity.filing_id,
            "filed": identity.filed,
            "reportUrl": identity.report_url,
            "year": identity.year,
        })
        return entry

    def discover(self, identity: FilingIdentity) -> dict[str, Any]:
        entry = self.entry(identity)
        entry["lastDiscoveredAt"] = utc_now()
        entry.setdefault("state", "discovered")
        entry.setdefault("attempts", 0)
        entry.setdefault("errors", [])
        return entry

    def should_process(self, identity: FilingIdentity, *, known_success: bool) -> bool:
        entry = self.entry(identity)
        if entry.get("state") in {"failed", "partial"}:
            return True
        if entry.get("parserVersion") and entry.get("parserVersion") != self.parser_version:
            return True
        if entry.get("forceRetry") is True:
            return True
        if not known_success:
            return True
        return False

    def begin(self, identity: FilingIdentity) -> None:
        entry = self.discover(identity)
        entry["state"] = "downloading"
        entry["lastAttemptAt"] = utc_now()
        entry["attempts"] = int(entry.get("attempts") or 0) + 1
        entry["forceRetry"] = False

    def success(self, identity: FilingIdentity, *, digest: str, trade_count: int) -> None:
        entry = self.entry(identity)
        previous_digest = entry.get("contentHash")
        entry.update({
            "state": "parsed",
            "parserVersion": self.parser_version,
            "contentHash": digest,
            "contentChanged": bool(previous_digest and previous_digest != digest),
            "tradeCount": int(trade_count),
            "lastSuccessfulAt": utc_now(),
            "lastError": None,
            "nextRetryAt": None,
        })

    def partial(self, identity: FilingIdentity, *, digest: str, trade_count: int, error: str) -> None:
        self.success(identity, digest=digest, trade_count=trade_count)
        entry = self.entry(identity)
        entry["state"] = "partial"
        entry["lastError"] = str(error)[:1000]
        entry["nextRetryAt"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(timespec="seconds")

    def failure(self, identity: FilingIdentity, error: Exception | str) -> None:
        entry = self.entry(identity)
        message = str(error)[:1000]
        errors = list(entry.get("errors") or [])
        errors.append({"at": utc_now(), "message": message})
        entry.update({
            "state": "failed",
            "lastError": message,
            "errors": errors[-10:],
            "nextRetryAt": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(timespec="seconds"),
        })

    def bootstrap_success(self, identity: FilingIdentity, *, trade_count: int) -> None:
        entry = self.entry(identity)
        if entry.get("state"):
            return
        entry.update({
            "state": "parsed",
            "parserVersion": self.parser_version,
            "contentHash": None,
            "contentChanged": False,
            "tradeCount": int(trade_count),
            "lastSuccessfulAt": None,
            "lastError": None,
            "nextRetryAt": None,
            "legacyBootstrap": True,
        })

    def summary(self) -> dict[str, Any]:
        entries = list(self.data.get("filings", {}).values())
        states: dict[str, int] = {}
        for entry in entries:
            state = str(entry.get("state") or "discovered")
            states[state] = states.get(state, 0) + 1
        retryable = [entry for entry in entries if entry.get("state") in {"failed", "partial"}]
        return {
            "parserVersion": self.parser_version,
            "filings": len(entries),
            "states": states,
            "retryable": len(retryable),
            "retryableFilings": [
                {
                    "trackerId": item.get("trackerId"),
                    "chamber": item.get("chamber"),
                    "filingId": item.get("filingId"),
                    "state": item.get("state"),
                    "lastError": item.get("lastError"),
                    "nextRetryAt": item.get("nextRetryAt"),
                    "reportUrl": item.get("reportUrl"),
                }
                for item in retryable[:50]
            ],
        }

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["schemaVersion"] = 1
        self.data["parserVersion"] = self.parser_version
        self.data["updatedAt"] = utc_now()
        self.data["summary"] = self.summary()
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def identity_from_filing(filing: Any) -> FilingIdentity:
    return FilingIdentity(
        tracker_id=str(filing.tracker_id),
        chamber=str(filing.chamber),
        filing_id=str(filing.filing_id),
        filed=str(filing.filed),
        report_url=str(filing.report_url),
        year=int(filing.year),
    )
