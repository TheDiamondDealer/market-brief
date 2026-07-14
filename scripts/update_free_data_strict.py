#!/usr/bin/env python3
"""Compatibility entrypoint for the exact-registry free-data collector.

BR-06 removes the former name-pattern monkey patch. Both this entrypoint and the
chart collector now install the same code-and-name registry selector.
"""

from __future__ import annotations

import sys

import update_free_data as collector
import update_free_data_api  # noqa: F401 - installs exact registry collection

if __name__ == "__main__":
    sys.exit(collector.main())
