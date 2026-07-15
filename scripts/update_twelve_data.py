#!/usr/bin/env python3
"""CLI for the private internal Twelve Data equity watchlist."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from twelve_data_core import *  # noqa: F401,F403
from twelve_data_metrics import *  # noqa: F401,F403
from twelve_data_pipeline import *  # noqa: F401,F403
from twelve_data_browser import write_js

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("disabled", "snapshot", "full"), default="full")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-js", type=Path, default=DEFAULT_JS)
    parser.add_argument("--reason", default="Private market-data collection has not been activated.")
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--request-interval", type=float, default=float(os.getenv("TWELVE_DATA_REQUEST_INTERVAL_SECONDS", "8.1")))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("TWELVE_DATA_TIMEOUT_SECONDS", "45")))
    parser.add_argument("--api-base", default=os.getenv("TWELVE_DATA_API_BASE", DEFAULT_API_BASE))
    args = parser.parse_args()

    config = read_json(args.config)
    items = validate_watchlist(config)
    if args.max_symbols > 0:
        items = items[: args.max_symbols]
    previous = read_json(args.output_json)
    now = utc_now()

    if args.mode == "disabled":
        payload = disabled_payload(items, now=now, reason=args.reason)
    else:
        key = os.getenv("TWELVE_DATA_API_KEY", "")
        client = TwelveDataClient(
            key,
            base_url=args.api_base,
            request_interval_seconds=args.request_interval,
            timeout_seconds=args.timeout,
        )
        payload = collect_payload(items, client=client, previous=previous, mode=args.mode, now=now)

    write_json(args.output_json, payload)
    write_js(args.output_js, payload)
    print(
        f"Twelve Data cache mode={payload['collection']['mode']} "
        f"status={payload['collection']['status']} "
        f"success={payload['collection']['successCount']} "
        f"failed={payload['collection']['failureCount']} "
        f"quotes={payload['collection']['freshQuoteCount']} "
        f"history={payload['collection']['freshHistoryCount']} "
        f"stale={payload['collection']['staleCount']} "
        f"generatedAtUtc={payload['generatedAtUtc']}"
    )
    return collection_exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
