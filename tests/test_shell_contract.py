from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "site" / "index.html"


class ShellContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.desktop_routes: set[str] = set()
        self.mobile_routes: set[str] = set()
        self.desktop_buttons: list[dict[str, str | None]] = []
        self.skip_target: str | None = None
        self.in_desktop_nav = False

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(str(element_id))
        if tag == "nav" and values.get("id") == "nav":
            self.in_desktop_nav = True
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.links.append(str(values["href"]))
        if tag == "script" and values.get("src"):
            self.scripts.append(str(values["src"]))
        if tag == "a" and values.get("class") == "skip-link":
            self.skip_target = values.get("href")
        if tag == "button" and values.get("data-view"):
            self.desktop_routes.add(str(values["data-view"]))
            self.desktop_buttons.append(values)
        if tag == "button" and values.get("data-shell-view"):
            self.mobile_routes.add(str(values["data-shell-view"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav" and self.in_desktop_nav:
            self.in_desktop_nav = False


class SharedShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.parser = ShellContractParser()
        cls.parser.feed(cls.html)

    def test_shared_styles_load_in_safe_order(self) -> None:
        links = self.parser.links
        self.assertLess(links.index("styles/tokens.css"), links.index("styles/base.css"))
        self.assertLess(links.index("styles/base.css"), links.index("styles.css"))
        self.assertEqual(links[-1], "styles/shell.css")

    def test_page_header_and_skip_link_exist(self) -> None:
        required_ids = {"main-content", "pageTitle", "pageSubtitle", "search", "freshness"}
        self.assertTrue(required_ids.issubset(self.parser.ids), required_ids - self.parser.ids)
        self.assertEqual(self.parser.skip_target, "#main-content")
        self.assertIn('aria-live="polite"', self.html)

    def test_desktop_navigation_has_accessible_names_and_tooltips(self) -> None:
        self.assertTrue(self.parser.desktop_buttons)
        for button in self.parser.desktop_buttons:
            with self.subTest(route=button.get("data-view")):
                self.assertTrue(button.get("aria-label"))
                self.assertTrue(button.get("title"))
                self.assertTrue(button.get("data-tooltip"))

    def test_mobile_navigation_reaches_every_desktop_route(self) -> None:
        missing = self.parser.desktop_routes - self.parser.mobile_routes
        self.assertEqual(missing, set())
        primary = {"home", "news", "events", "cot", "trackers"}
        self.assertTrue(primary.issubset(self.parser.mobile_routes))
        self.assertIn('role="dialog"', self.html)
        self.assertIn('aria-modal="true"', self.html)

    def test_shell_behaviour_loads_after_existing_consumers(self) -> None:
        scripts = self.parser.scripts
        self.assertEqual(scripts[-1], "shell.js")
        self.assertLess(scripts.index("app.js"), scripts.index("shell.js"))
        self.assertLess(scripts.index("intelligence-app.js"), scripts.index("shell.js"))
        self.assertLess(scripts.index("command-centre.js"), scripts.index("shell.js"))

    def test_token_layer_keeps_legacy_feature_aliases(self) -> None:
        tokens = (ROOT / "site" / "styles" / "tokens.css").read_text(encoding="utf-8")
        required = {
            "--bg-canvas", "--bg-panel", "--border-subtle", "--text-primary",
            "--accent", "--positive", "--negative", "--rail-width", "--header-height",
            "--bg: var(--bg-canvas)", "--teal: var(--accent)",
        }
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, tokens)

    def test_shell_responsive_contract_is_explicit(self) -> None:
        shell = (ROOT / "site" / "styles" / "shell.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 1279px)", shell)
        self.assertIn("@media (max-width: 899px)", shell)
        self.assertIn("@media (max-width: 599px)", shell)
        self.assertIn("mobile-bottom-nav", shell)
        self.assertIn("min-height: 54px", shell)


if __name__ == "__main__":
    unittest.main()
