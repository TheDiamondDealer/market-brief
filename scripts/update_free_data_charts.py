#!/usr/bin/env python3
"""Extend the official free-data collector with chart-ready COT history.

This module imports the current CFTC API collector, then augments every valid
market summary with the latest 52 weekly long, short and net observations. The
existing validation and stale-contract exclusions remain unchanged.
"""

from __future__ import annotations

import sys

import update_free_data as collector
import update_free_data_api  # noqa: F401 - installs the current official CFTC API collector

CHART_HISTORY_WEEKS = 52
_original_summarise_market = collector.summarise_market


def summarise_market_with_history(market_id, label, observations):
    summary = _original_summarise_market(market_id, label, observations)
    if not summary:
        return None

    deduped = {}
    for observation in observations:
        deduped[observation.date] = observation
    ordered = sorted(deduped.values(), key=lambda item: item.date)[-CHART_HISTORY_WEEKS:]

    summary["history52"] = [
        {
            "date": observation.date,
            "long": round(observation.long),
            "short": round(observation.short),
            "net": round(observation.net),
        }
        for observation in ordered
    ]
    return summary


collector.summarise_market = summarise_market_with_history


if __name__ == "__main__":
    sys.exit(collector.main())
