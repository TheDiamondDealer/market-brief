#!/usr/bin/env python3
"""AI news-impact tagger (PR-2 pipeline core).

Classifies unstructured news headlines (GDELT radar + conflict watch) against
the closed asset vocabulary in ``asset_board.json`` using the Anthropic Messages
API (model ``claude-haiku-4-5``), and maintains an append-only, self-contained,
7-day rolling ledger at ``site/data/impact-tags.json``.

Design contract:
- STDLIB ONLY. HTTP is raw ``urllib`` (matches every collector in ``scripts/``).
- The public ``tag_pending`` accepts an injectable ``caller`` so tests never hit
  the network.
- FAIL-OPEN: a missing ``ANTHROPIC_API_KEY`` or any API error prints a notice,
  writes a valid ledger, and exits 0 — a model outage must never break the
  static-site build. A whole-batch outage does NOT burn per-item attempts.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from validate_impact_tags import valid_asset_ids, validate_item_output

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SITE = ROOT / "site"
ASSET_BOARD = SCRIPTS / "asset_board.json"
GDELT_PATH = SITE / "data" / "gdelt-radar.json"
CONFLICT_PATH = SITE / "data" / "conflict-watch.json"
LEDGER_PATH = SITE / "data" / "impact-tags.json"

MODEL = "claude-haiku-4-5"
SCHEMA_VERSION = 1
MAX_ATTEMPTS = 3
PRUNE_DAYS = 7


# --------------------------------------------------------------------------- #
# I/O helpers (always utf-8 — Windows default cp1252 chokes on the feeds)
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# --------------------------------------------------------------------------- #
# Input normalization
# --------------------------------------------------------------------------- #
def normalize_gdelt(data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for art in data.get("articles", []) or []:
        if not isinstance(art, dict) or not art.get("id"):
            continue
        topics = art.get("topics") or []
        topic = topics[0] if topics else ""
        rows.append({
            "id": str(art["id"]),
            "source": "gdelt",
            "headline": str(art.get("title", "")),
            "url": str(art.get("url", "")),
            "domain": str(art.get("domain", "")),
            "seenAt": str(art.get("seenAt", "")),
            "topic": str(topic),
        })
    return rows


def normalize_conflict(data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in data.get("items", []) or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        source = item.get("source")
        if isinstance(source, dict):
            source_name = str(source.get("name") or source.get("id") or "conflict-watch")
        else:
            source_name = str(source or "conflict-watch")
        rows.append({
            "id": str(item["id"]),
            "source": "conflict-watch",
            "headline": str(item.get("title", "")),
            "url": str(item.get("url", "")),
            "domain": source_name,
            "seenAt": str(item.get("publishedAt", "")),
            "topic": source_name,
        })
    return rows


def collect_inputs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if GDELT_PATH.exists():
        rows.extend(normalize_gdelt(load_json(GDELT_PATH)))
    if CONFLICT_PATH.exists():
        rows.extend(normalize_conflict(load_json(CONFLICT_PATH)))
    # de-dup by id, first occurrence wins
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        unique.append(row)
    return unique


# --------------------------------------------------------------------------- #
# Ledger housekeeping
# --------------------------------------------------------------------------- #
def empty_ledger(now: datetime) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAtUtc": _iso(now),
        "model": MODEL,
        "items": [],
    }


def load_ledger(now: datetime) -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        return empty_ledger(now)
    try:
        ledger = load_json(LEDGER_PATH)
    except (ValueError, OSError):
        return empty_ledger(now)
    if not isinstance(ledger, dict) or not isinstance(ledger.get("items"), list):
        return empty_ledger(now)
    return ledger


def prune_ledger(ledger: dict[str, Any], now: datetime, days: int = PRUNE_DAYS) -> dict[str, Any]:
    """Drop items whose ``seenAt`` is older than ``days`` before ``now``.

    Unparseable dates are KEPT (fail-safe — never silently lose an item).
    """
    cutoff = now - timedelta(days=days)
    kept: list[dict[str, Any]] = []
    for item in ledger.get("items", []):
        dt = _parse_iso(item.get("seenAt"))
        if dt is None or dt >= cutoff:
            kept.append(item)
    ledger["items"] = kept
    return ledger


def select_pending(ledger: dict[str, Any], inputs: list[dict[str, str]]) -> list[dict[str, str]]:
    """Items to (re)send: absent from ledger, or ``tagFailed`` with attempts < cap."""
    index = {i["id"]: i for i in ledger.get("items", [])}
    pending: list[dict[str, str]] = []
    for row in inputs:
        entry = index.get(row["id"])
        if entry is None:
            pending.append(row)
        elif entry.get("tagState") == "tagFailed" and entry.get("attempts", 0) < MAX_ATTEMPTS:
            pending.append(row)
    return pending


def _ensure_entry(ledger: dict[str, Any], index: dict[str, Any], row: dict[str, str]) -> dict[str, Any]:
    entry = index.get(row["id"])
    if entry is not None:
        return entry
    entry = {
        "id": row["id"],
        "source": row.get("source", ""),
        "headline": row.get("headline", ""),
        "url": row.get("url", ""),
        "domain": row.get("domain", ""),
        "seenAt": row.get("seenAt", ""),
        "topic": row.get("topic", ""),
        "tagState": "tagFailed",
        "attempts": 0,
        "taggedAtUtc": None,
        "tags": [],
    }
    ledger.setdefault("items", []).append(entry)
    index[row["id"]] = entry
    return entry


# --------------------------------------------------------------------------- #
# Anthropic Messages API (raw urllib) + prompt
# --------------------------------------------------------------------------- #
def call_claude(prompt: str, *, timeout: int = 60) -> str:
    """Raw Messages API call. Returns the assistant text. Raises on any failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    parts = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
    return "".join(parts)


def build_prompt(registry: dict[str, Any], pending_items: list[dict[str, str]]) -> str:
    assets = [a for a in registry.get("assets", []) if isinstance(a, dict) and a.get("id")]
    vocab = "\n".join(f"- {a['id']} — {a.get('label', a['id'])}" for a in assets)
    lines = []
    for idx, item in enumerate(pending_items, start=1):
        lines.append(
            f"{idx}. itemId={item['id']}\n"
            f"   headline: {item.get('headline', '')}\n"
            f"   source domain: {item.get('domain', '')}\n"
            f"   topic: {item.get('topic', '')}\n"
            f"   seenAt: {item.get('seenAt', '')}"
        )
    items_block = "\n".join(lines)
    return (
        "You tag financial-news headlines for their directional impact on a CLOSED "
        "list of assets. Use ONLY these asset ids (never invent one):\n"
        f"{vocab}\n\n"
        "For each numbered item below, decide which listed assets the headline moves "
        "and in which direction. An empty tags array is a valid, expected answer when "
        "there is no clear asset impact.\n\n"
        f"{items_block}\n\n"
        "Return STRICT JSON ONLY — no prose, no markdown fences — as an array:\n"
        '[{"itemId": "<id from above>", "tags": [{"assetId": "<one listed id>", '
        '"direction": "up|down|mixed", "confidence": "high|medium|low", '
        '"mechanism": "<one concise sentence>"}]}]\n'
    )


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1] if "\n" in stripped else ""
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def _parse_output_by_id(text: str) -> dict[str, Any]:
    """Parse the model text into ``{itemId: raw_item_obj}``.

    Returns ``{}`` on any parse failure so every pending item is treated as
    absent from the output (i.e. malformed → tagFailed).
    """
    try:
        parsed = json.loads(_strip_fences(text))
    except (ValueError, TypeError):
        return {}
    if not isinstance(parsed, list):
        return {}
    by_id: dict[str, Any] = {}
    for obj in parsed:
        if isinstance(obj, dict) and isinstance(obj.get("itemId"), str):
            by_id[obj["itemId"]] = obj
    return by_id


# --------------------------------------------------------------------------- #
# Core state machine
# --------------------------------------------------------------------------- #
def tag_pending(
    ledger: dict[str, Any],
    pending_items: list[dict[str, str]],
    *,
    caller: Callable[[str], str] = call_claude,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Send pending items to the model in one batched call and fold results in.

    Fail-open: if the caller raises (missing key, network, non-200, bad JSON,
    timeout) this is a whole-batch OUTAGE — leave every pending item untouched
    (no new entries, no attempts burned) and return the ledger unchanged.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if not pending_items:
        return ledger

    registry = load_json(ASSET_BOARD)
    valid_ids = valid_asset_ids(registry)
    prompt = build_prompt(registry, pending_items)

    try:
        text = caller(prompt)
    except Exception as exc:  # noqa: BLE001 — outage of any kind must fail open
        print(
            f"[tag_impacts] model call failed ({exc.__class__.__name__}: {exc}); "
            f"leaving {len(pending_items)} pending item(s) untagged this run."
        )
        return ledger

    by_id = _parse_output_by_id(text)
    index = {i["id"]: i for i in ledger.get("items", [])}

    for row in pending_items:
        raw = by_id.get(row["id"])
        result = validate_item_output(raw, valid_ids) if raw is not None else None
        entry = _ensure_entry(ledger, index, row)
        if result is None:
            # Malformed / missing model output for this item → tagFailed, burn one attempt.
            entry["attempts"] = entry.get("attempts", 0) + 1
            entry["taggedAtUtc"] = None
            entry["tagState"] = "unavailable" if entry["attempts"] >= MAX_ATTEMPTS else "tagFailed"
        else:
            entry["tagState"] = "tagged"
            entry["tags"] = result
            entry["taggedAtUtc"] = _iso(now)
    return ledger


def write_ledger(ledger: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run(*, caller: Callable[[str], str] = call_claude, now: datetime | None = None) -> int:
    if now is None:
        now = datetime.now(timezone.utc)
    ledger = load_ledger(now)
    prune_ledger(ledger, now)
    inputs = collect_inputs()
    pending = select_pending(ledger, inputs)
    print(
        f"[tag_impacts] {len(inputs)} input item(s), {len(pending)} pending, "
        f"{len(ledger['items'])} in ledger after prune."
    )
    tag_pending(ledger, pending, caller=caller, now=now)
    ledger["schemaVersion"] = SCHEMA_VERSION
    ledger["model"] = MODEL
    ledger["generatedAtUtc"] = _iso(now)
    write_ledger(ledger)
    tagged = sum(1 for i in ledger["items"] if i.get("tagState") == "tagged")
    print(f"[tag_impacts] wrote {LEDGER_PATH.relative_to(ROOT)} ({tagged} tagged, {len(ledger['items'])} total).")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
