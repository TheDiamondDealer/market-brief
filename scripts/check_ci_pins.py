#!/usr/bin/env python3
"""Fail CI when workflow actions or direct Python dependencies are unpinned."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REQUIREMENTS = ROOT / "requirements"

USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
IMMUTABLE_ACTION_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
PINNED_REQUIREMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+==[^\s;]+(?:\s*;.*)?$")


def workflow_errors() -> list[str]:
    errors: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        for target in USES_RE.findall(text):
            if target.startswith("./"):
                continue
            if not IMMUTABLE_ACTION_RE.fullmatch(target):
                errors.append(f"{path.relative_to(ROOT)}: action is not pinned to a 40-character SHA: {target}")

        for line_number, line in enumerate(text.splitlines(), start=1):
            if "python -m pip install" not in line:
                continue
            if "requirements/" not in line or "-r " not in line and "--requirement " not in line:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: install dependencies through a pinned requirements file"
                )
    return errors


def requirement_errors() -> list[str]:
    errors: list[str] = []
    files = sorted(REQUIREMENTS.glob("*.txt"))
    if not files:
        return ["requirements/: no pinned dependency files found"]

    for path in files:
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-r ") or line.startswith("--requirement "):
                continue
            if not PINNED_REQUIREMENT_RE.fullmatch(line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: dependency must use an exact == version: {line}"
                )
    return errors


def main() -> int:
    errors = workflow_errors() + requirement_errors()
    if errors:
        print("CI pin validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Validated immutable GitHub Action references and exact Python dependency pins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
