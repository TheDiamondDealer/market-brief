#!/usr/bin/env python3
"""Pure validation helpers for the news-impact tagger (PR-2).

No I/O, no network, no third-party deps: every function is a deterministic
transform of already-parsed data so the tagger and its unit tests can share the
same closed-vocabulary rules.
"""
from __future__ import annotations

from typing import Any

DIRECTIONS = {"up", "down", "mixed"}
CONFIDENCES = {"high", "medium", "low"}
TAG_KEYS = ("assetId", "direction", "confidence", "mechanism")


def valid_asset_ids(registry: dict[str, Any]) -> set[str]:
    """Return the set of allowed ``assetId`` values from ``asset_board.json``."""
    assets = registry.get("assets", []) if isinstance(registry, dict) else []
    return {a["id"] for a in assets if isinstance(a, dict) and a.get("id")}


def validate_tag(tag: Any, valid_ids: set[str]) -> bool:
    """True only for a well-formed tag against the closed vocabulary."""
    if not isinstance(tag, dict):
        return False
    if tag.get("assetId") not in valid_ids:
        return False
    if tag.get("direction") not in DIRECTIONS:
        return False
    if tag.get("confidence") not in CONFIDENCES:
        return False
    mechanism = tag.get("mechanism")
    if not isinstance(mechanism, str) or not mechanism.strip():
        return False
    return True


def clean_tag(tag: dict[str, Any]) -> dict[str, str]:
    """Project a validated tag down to exactly the four ledger keys."""
    return {
        "assetId": tag["assetId"],
        "direction": tag["direction"],
        "confidence": tag["confidence"],
        "mechanism": tag["mechanism"].strip(),
    }


def validate_item_output(raw_obj: Any, valid_ids: set[str]) -> list[dict[str, str]] | None:
    """Validate one model item object.

    Returns the filtered (possibly empty) list of clean tags, or ``None`` if the
    object itself is malformed so the caller can mark the item ``tagFailed``.
    """
    if not isinstance(raw_obj, dict):
        return None
    tags = raw_obj.get("tags")
    if not isinstance(tags, list):
        return None
    return [clean_tag(t) for t in tags if validate_tag(t, valid_ids)]
