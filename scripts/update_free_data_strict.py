#!/usr/bin/env python3
"""Run the free-data collector with strict primary-contract CFTC matching.

The CFTC files contain micro, mini, cross-rate, ICE and ultra variants whose
names can overlap the primary contracts. This wrapper narrows the matching
without duplicating the collector implementation.
"""

from __future__ import annotations

import sys

import update_free_data as collector

collector.DISAGG_MARKETS = {
    "gold": {
        "label": "Gold",
        "prefix": "GOLD -",
        "patterns": ["COMMODITY EXCHANGE"],
        "excludes": ["MICRO", "MINI"],
    },
    "silver": {
        "label": "Silver",
        "prefix": "SILVER -",
        "patterns": ["COMMODITY EXCHANGE"],
        "excludes": ["MICRO", "MINI"],
    },
    "copper": {
        "label": "Copper",
        "patterns": ["COPPER", "COMMODITY EXCHANGE"],
        "excludes": ["MICRO", "MINI"],
    },
    "oil": {
        "label": "WTI crude oil",
        "prefix": "CRUDE OIL, LIGHT SWEET",
        "patterns": ["NEW YORK MERCANTILE"],
        "excludes": ["E-MINI", "MICRO", "ICE FUTURES"],
    },
    "natural-gas": {
        "label": "Natural gas",
        "prefix": "NATURAL GAS -",
        "patterns": ["NEW YORK MERCANTILE"],
        "excludes": ["E-MINI", "MICRO"],
    },
}

collector.TFF_MARKETS = {
    "yen": {
        "label": "Japanese yen",
        "prefix": "JAPANESE YEN -",
        "excludes": ["EURO FX", "CROSS"],
    },
    "us10y-futures": {
        "label": "US 10-year Treasury futures",
        "prefix": "10-YEAR U.S. TREASURY NOTES -",
        "patterns": ["CHICAGO BOARD OF TRADE"],
        "excludes": ["ULTRA"],
    },
    "usd-index": {
        "label": "US Dollar Index",
        "prefix": "USD INDEX -",
        "patterns": ["ICE FUTURES U.S."],
    },
}


def strict_market_matches(name: str, config: dict) -> bool:
    upper = name.upper().strip()
    prefix = str(config.get("prefix", "")).upper()
    excludes = [str(value).upper() for value in config.get("excludes", [])]
    all_patterns = [str(value).upper() for value in config.get("patterns", [])]
    any_patterns = [str(value).upper() for value in config.get("patterns_any", [])]

    if prefix and not upper.startswith(prefix):
        return False
    if any(value in upper for value in excludes):
        return False
    if all_patterns and not all(value in upper for value in all_patterns):
        return False
    if any_patterns and not any(value in upper for value in any_patterns):
        return False
    return True


collector.market_matches = strict_market_matches

if __name__ == "__main__":
    sys.exit(collector.main())
