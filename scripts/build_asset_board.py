"""Emit site/asset-board-data.js from scripts/asset_board.json.

The emitted file is generated — never hand-edit it. Change the registry
JSON and re-run: python scripts/build_asset_board.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "asset_board.json"
TARGET = ROOT / "site" / "asset-board-data.js"


def emit() -> str:
    registry = json.loads(SOURCE.read_text(encoding="utf-8"))
    compact = json.dumps(registry, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    return f"window.marketAssetBoard = {compact};\n"


def main() -> None:
    TARGET.write_text(emit(), encoding="utf-8", newline="\n")
    print(f"Wrote {TARGET} ({TARGET.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
