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

from validate_impact_tags import CONFIDENCES, DIRECTIONS, clean_note, valid_asset_ids, validate_item_output

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SITE = ROOT / "site"
ASSET_BOARD = SCRIPTS / "asset_board.json"
GDELT_PATH = SITE / "data" / "gdelt-radar.json"
CONFLICT_PATH = SITE / "data" / "conflict-watch.json"
LEDGER_PATH = SITE / "data" / "impact-tags.json"

MODEL = "claude-haiku-4-5"
SCHEMA_VERSION = 2
MAX_ATTEMPTS = 3
PRUNE_DAYS = 7
MAX_TOKENS = 8192
# Token-aware chunking: cap items per model call so the response never hits the
# output-token ceiling. A batch closes at BATCH_SIZE items OR MAX_BATCH_CHARS of
# headline text, whichever comes first (long headlines close a batch early).
BATCH_SIZE = 15
MAX_BATCH_CHARS = 4000


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
        "note": "",
        "tags": [],
    }
    ledger.setdefault("items", []).append(entry)
    index[row["id"]] = entry
    return entry


# --------------------------------------------------------------------------- #
# Anthropic Messages API (raw urllib) + prompt
# --------------------------------------------------------------------------- #
SYSTEM_INSTRUCTION = (
    "You tag financial-news headlines for their directional impact on a CLOSED list "
    "of assets. Use ONLY the asset ids allowed by the tool schema — never invent one. "
    "For every supplied itemId return exactly one result object; an empty tags array "
    "is a valid, expected answer when the headline has no clear asset impact. "
    "Also return a `note`: one or two plain-English sentences on how the headline "
    "transmits to the assets you tagged — the net 'why it matters'. Ground the note "
    "ONLY in the assets you tagged; never mention an asset you did not tag. If you "
    "return no tags, return an empty note."
)


def build_tool(valid_ids: set[str]) -> dict[str, Any]:
    """A forced tool whose schema pins assetId/direction/confidence to closed enums,
    so the model physically cannot return an unlisted asset or malformed JSON — the
    old free-text-JSON path could truncate or fence-wrap and lose the whole batch."""
    return {
        "name": "record_impact_tags",
        "description": "Record the directional market impact of each supplied news headline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "itemId": {"type": "string"},
                            "note": {
                                "type": "string",
                                "description": "One or two plain sentences on why this headline matters for the assets you tagged; empty string when there are no tags.",
                            },
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "assetId": {"type": "string", "enum": sorted(valid_ids)},
                                        "direction": {"type": "string", "enum": sorted(DIRECTIONS)},
                                        "confidence": {"type": "string", "enum": sorted(CONFIDENCES)},
                                        "mechanism": {"type": "string"},
                                    },
                                    "required": ["assetId", "direction", "confidence", "mechanism"],
                                },
                            },
                        },
                        "required": ["itemId", "tags"],
                    },
                },
            },
            "required": ["results"],
        },
        # Cache the tool + system prefix across a run's chunks. The vocab is below
        # Haiku's ~2048-token cache minimum today, so this is currently a no-op, but it
        # costs nothing and engages automatically if the asset list ever grows.
        "cache_control": {"type": "ephemeral"},
    }


def build_user_message(pending_items: list[dict[str, str]]) -> str:
    lines = [
        f"itemId={item['id']}\n"
        f"   headline: {item.get('headline', '')}\n"
        f"   source domain: {item.get('domain', '')}\n"
        f"   topic: {item.get('topic', '')}\n"
        f"   seenAt: {item.get('seenAt', '')}"
        for item in pending_items
    ]
    return "Tag these items:\n\n" + "\n\n".join(lines)


def call_model(pending_items: list[dict[str, str]], valid_ids: set[str], *, timeout: int = 90) -> dict[str, Any]:
    """Forced-tool Messages API call → ``{"results": [...], "stopReason": str}``.

    Raises on any transport/API failure so a whole-chunk outage fails open upstream.
    Structured tool output means there is no free text to parse and no fences to strip.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": SYSTEM_INSTRUCTION, "cache_control": {"type": "ephemeral"}}],
        "tools": [build_tool(valid_ids)],
        "tool_choice": {"type": "tool", "name": "record_impact_tags"},
        "messages": [{"role": "user", "content": build_user_message(pending_items)}],
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
    tool_block = next(
        (b for b in payload.get("content", [])
         if b.get("type") == "tool_use" and b.get("name") == "record_impact_tags"),
        None,
    )
    results = tool_block.get("input", {}).get("results", []) if tool_block else []
    return {"results": results if isinstance(results, list) else [], "stopReason": payload.get("stop_reason")}


def _results_by_id(results: list[Any]) -> dict[str, Any]:
    by_id: dict[str, Any] = {}
    for obj in results:
        if isinstance(obj, dict) and isinstance(obj.get("itemId"), str):
            by_id[obj["itemId"]] = obj
    return by_id


def plan_batches(pending_items: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Token-aware chunking: close a batch at BATCH_SIZE items or MAX_BATCH_CHARS of
    headline text, whichever comes first, so long headlines never overflow a call."""
    batches: list[list[dict[str, str]]] = []
    batch: list[dict[str, str]] = []
    chars = 0
    for item in pending_items:
        cost = len(str(item.get("headline", ""))) + 80  # headline + per-item framing
        if batch and (len(batch) >= BATCH_SIZE or chars + cost > MAX_BATCH_CHARS):
            batches.append(batch)
            batch, chars = [], 0
        batch.append(item)
        chars += cost
    if batch:
        batches.append(batch)
    return batches


# --------------------------------------------------------------------------- #
# Core state machine
# --------------------------------------------------------------------------- #
def tag_pending(
    ledger: dict[str, Any],
    pending_items: list[dict[str, str]],
    *,
    caller: Callable[..., dict[str, Any]] = call_model,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Tag pending items in token-aware chunks and fold results in.

    ``caller(items, valid_ids)`` returns ``{"results": [...], "stopReason": str}``.
    Fail-open: if the caller raises (missing key, network, non-200, timeout) that is
    a whole-chunk OUTAGE — leave only that chunk's items untouched (no attempts burned)
    and carry on with the other chunks.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if not pending_items:
        return ledger

    registry = load_json(ASSET_BOARD)
    valid_ids = valid_asset_ids(registry)
    index = {i["id"]: i for i in ledger.get("items", [])}
    tagged_n = dropped_n = truncated_n = 0

    for chunk in plan_batches(pending_items):
        try:
            response = caller(chunk, valid_ids)
        except Exception as exc:  # noqa: BLE001 — outage of any kind must fail open
            print(
                f"[tag_impacts] model call failed ({exc.__class__.__name__}: {exc}); "
                f"leaving {len(chunk)} pending item(s) untagged this run."
            )
            continue

        results = response.get("results", []) if isinstance(response, dict) else []
        if isinstance(response, dict) and response.get("stopReason") == "max_tokens":
            truncated_n += 1
            print(
                f"[tag_impacts] a chunk of {len(chunk)} hit max_tokens; "
                "items missing from the truncated result will retry next run."
            )
        by_id = _results_by_id(results)
        for row in chunk:
            raw = by_id.get(row["id"])
            result = validate_item_output(raw, valid_ids) if raw is not None else None
            entry = _ensure_entry(ledger, index, row)
            if result is None:
                # Missing (truncated) or schema-invalid output for this item → tagFailed.
                entry["attempts"] = entry.get("attempts", 0) + 1
                entry["taggedAtUtc"] = None
                entry["tagState"] = "unavailable" if entry["attempts"] >= MAX_ATTEMPTS else "tagFailed"
                dropped_n += 1
            else:
                entry["tagState"] = "tagged"
                entry["tags"] = result
                entry["note"] = clean_note(raw)
                entry["taggedAtUtc"] = _iso(now)
                tagged_n += 1

    if dropped_n or truncated_n:
        note = f", {truncated_n} chunk(s) truncated" if truncated_n else ""
        print(f"[tag_impacts] tagged {tagged_n}, dropped {dropped_n} this run{note}.")
    return ledger


def write_ledger(ledger: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run(*, caller: Callable[..., dict[str, Any]] = call_model, now: datetime | None = None) -> int:
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
