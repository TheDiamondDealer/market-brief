#!/usr/bin/env python3
"""Offline production audit for the static Market Brief shell."""
from __future__ import annotations

import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
INDEX = SITE / "index.html"
LOADER = SITE / "core" / "feature-loader.js"

FILE_BUDGETS = {
    "index.html": 250_000,
    "political-data.js": 1_500_000,
    "equity-data.js": 2_000_000,
    "core/feature-loader.js": 50_000,
    "core/freshness.js": 80_000,
}
FEATURE_BUDGET = 140_000
TOTAL_RUNTIME_BUDGET = 4_000_000
GENERATED_RUNTIME_EXCLUSIONS = {
    SITE / "free-data.js",
    SITE / "political-data.js",
    SITE / "equity-data.js",
    SITE / "data" / "political-disclosures.json",
    SITE / "data" / "free-market-data.json",
    SITE / "data" / "equity-market-data.json",
}


class ShellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.scripts: list[str] = []
        self.styles: list[str] = []
        self.errors: list[str] = []
        self._button_stack: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        if attrs.get("id"):
            self.ids.append(str(attrs["id"]))
        if tag == "script" and attrs.get("src"):
            self.scripts.append(str(attrs["src"]))
        if tag == "link" and attrs.get("rel") == "stylesheet" and attrs.get("href"):
            self.styles.append(str(attrs["href"]))
        if tag == "a" and attrs.get("target") == "_blank":
            rel = set(str(attrs.get("rel") or "").split())
            if not {"noopener", "noreferrer"}.intersection(rel):
                self.errors.append(f"External link {attrs.get('href')} opens a new tab without rel=noopener/noreferrer")
        if tag == "img" and not attrs.get("alt"):
            self.errors.append(f"Image {attrs.get('src')} is missing alt text")
        if tag == "iframe":
            if not attrs.get("title"):
                self.errors.append(f"Iframe {attrs.get('src')} is missing a title")
            if attrs.get("loading") != "lazy":
                self.errors.append(f"Iframe {attrs.get('src')} is not lazy loaded")
        if tag == "input":
            if not any(attrs.get(key) for key in ("aria-label", "aria-labelledby", "placeholder", "title", "id")):
                self.errors.append("Input is missing an accessible name or stable id")
        if tag == "button":
            self._button_stack.append({"attrs": attrs, "text": []})

    def handle_data(self, data: str) -> None:
        if self._button_stack:
            self._button_stack[-1]["text"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "button" or not self._button_stack:
            return
        button = self._button_stack.pop()
        attrs = button["attrs"]
        text = "".join(button["text"]).strip()
        if not text and not any(attrs.get(key) for key in ("aria-label", "aria-labelledby", "title")):
            self.errors.append("Button has no visible or accessible name")


def local_path(reference: str) -> Path | None:
    if not reference or reference.startswith(("http://", "https://", "//", "data:", "#")):
        return None
    clean = reference.split("?", 1)[0].split("#", 1)[0]
    return SITE / clean


def audit_shell() -> list[str]:
    errors: list[str] = []
    parser = ShellParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    errors.extend(parser.errors)
    duplicates = sorted(item for item, count in Counter(parser.ids).items() if count > 1)
    if duplicates:
        errors.append(f"Duplicate HTML ids: {', '.join(duplicates)}")
    for kind, references in (("script", parser.scripts), ("stylesheet", parser.styles)):
        repeated = sorted(item for item, count in Counter(references).items() if count > 1)
        if repeated:
            errors.append(f"Duplicate {kind} references: {', '.join(repeated)}")
        for reference in references:
            path = local_path(reference)
            if path and not path.exists():
                errors.append(f"Missing local {kind}: {reference}")
    index_text = INDEX.read_text(encoding="utf-8")
    if "data/political-disclosures.json" in index_text:
        errors.append("Full political disclosure history must not be loaded by index.html")
    if 'href="#main-content"' not in index_text or 'id="main-content"' not in index_text:
        errors.append("Skip-link target is missing")
    if 'meta name="viewport"' not in index_text:
        errors.append("Responsive viewport metadata is missing")
    return errors


def manifest_assets() -> tuple[list[str], list[str]]:
    text = LOADER.read_text(encoding="utf-8")
    styles = re.findall(r"styles:\s*\[([^\]]*)\]", text)
    scripts = re.findall(r"scripts:\s*\[([^\]]*)\]", text)
    quoted = re.compile(r"['\"]([^'\"]+)['\"]")
    return (
        [match for group in styles for match in quoted.findall(group)],
        [match for group in scripts for match in quoted.findall(group)],
    )


def audit_manifest() -> list[str]:
    errors: list[str] = []
    styles, scripts = manifest_assets()
    for kind, references in (("feature stylesheet", styles), ("feature script", scripts)):
        repeated = sorted(item for item, count in Counter(references).items() if count > 1)
        if repeated:
            errors.append(f"Duplicate {kind}s: {', '.join(repeated)}")
        for reference in references:
            path = local_path(reference)
            if not path or not path.exists():
                errors.append(f"Missing {kind}: {reference}")
            elif path.stat().st_size > FEATURE_BUDGET:
                errors.append(f"{reference} exceeds {FEATURE_BUDGET:,} byte feature budget ({path.stat().st_size:,})")
    text = LOADER.read_text(encoding="utf-8")
    hardening_position = text.find("styles/hardening.css")
    feature_position = text.find("Promise.all(manifest.map(loadEntry))")
    if hardening_position < 0 or feature_position < 0:
        errors.append("Global hardening stylesheet is not in the ordered feature bootstrap")
    if "equity-data.js" not in text or "features/market-watch/market-watch-page.js" not in text:
        errors.append("Private equity feed is not connected through the ordered feature manifest")
    return errors


def audit_css_contract() -> list[str]:
    errors: list[str] = []
    css_path = SITE / "styles" / "hardening.css"
    if not css_path.exists():
        return ["styles/hardening.css is missing"]
    css = css_path.read_text(encoding="utf-8")
    for marker in (
        ":focus-visible",
        "prefers-reduced-motion:reduce",
        "forced-colors:active",
        "max-width:1440px",
        "max-width:1024px",
        "max-width:768px",
        "max-width:390px",
        "min-height:44px",
        "overflow-x:auto",
    ):
        if marker not in css:
            errors.append(f"Hardening CSS is missing {marker}")
    return errors


def audit_private_feed() -> list[str]:
    errors: list[str] = []
    for relative in ("equity-data.js", "data/equity-market-data.json"):
        path = SITE / relative
        if not path.exists():
            errors.append(f"Private market-data cache is missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        if "apikey=" in text or "twelve_data_api_key" in text:
            errors.append(f"Private market-data cache appears to contain a credential: {relative}")
    return errors


def audit_payloads() -> list[str]:
    errors: list[str] = []
    for relative, limit in FILE_BUDGETS.items():
        path = SITE / relative
        if not path.exists():
            errors.append(f"Budgeted runtime file is missing: {relative}")
            continue
        if path.stat().st_size > limit:
            errors.append(f"{relative} exceeds {limit:,} byte budget ({path.stat().st_size:,})")
    runtime_total = 0
    for path in SITE.rglob("*"):
        if not path.is_file() or path in GENERATED_RUNTIME_EXCLUSIONS:
            continue
        if "data" in path.relative_to(SITE).parts:
            continue
        if path.suffix.lower() in {".js", ".css", ".html"}:
            runtime_total += path.stat().st_size
    if runtime_total > TOTAL_RUNTIME_BUDGET:
        errors.append(f"Non-generated runtime exceeds {TOTAL_RUNTIME_BUDGET:,} byte budget ({runtime_total:,})")
    bootstrap = SITE / "political-data.js"
    full_history = SITE / "data" / "political-disclosures.json"
    if bootstrap.exists() and full_history.exists() and bootstrap.stat().st_size >= full_history.stat().st_size:
        errors.append("Political browser bootstrap is not smaller than retained full history")
    return errors


def main() -> int:
    errors = [
        *audit_shell(),
        *audit_manifest(),
        *audit_css_contract(),
        *audit_private_feed(),
        *audit_payloads(),
    ]
    if errors:
        print("Static production audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Static production audit passed")
    print(f"- index: {INDEX.stat().st_size:,} bytes")
    print(f"- political bootstrap: {(SITE / 'political-data.js').stat().st_size:,} bytes")
    print(f"- equity bootstrap: {(SITE / 'equity-data.js').stat().st_size:,} bytes")
    print(f"- feature assets: {sum(len(group) for group in manifest_assets())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
