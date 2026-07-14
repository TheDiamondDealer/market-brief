from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ShellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.views: set[str] = set()
        self.nav_routes: set[str] = set()
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "section" and str(values.get("id", "")).startswith("view-"):
            self.views.add(str(values["id"])[5:])
        if tag == "button" and values.get("data-view"):
            self.nav_routes.add(str(values["data-view"]))
        if tag == "script" and values.get("src"):
            self.scripts.append(str(values["src"]))


class FrontendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        cls.parser = ShellParser()
        cls.parser.feed(cls.html)

    def test_required_direct_routes_exist_in_navigation_and_shell(self) -> None:
        required = {"home", "news", "cot", "rates", "scenarios", "trackers"}
        self.assertTrue(required.issubset(self.parser.views), required - self.parser.views)
        self.assertTrue(required.issubset(self.parser.nav_routes), required - self.parser.nav_routes)

    def test_data_scripts_load_before_consumers(self) -> None:
        position = {name: index for index, name in enumerate(self.parser.scripts)}
        required_scripts = {
            "data.js",
            "command-centre-data.js",
            "intelligence-data.js",
            "politicians.js",
            "free-data.js",
            "app.js",
            "intelligence-app.js",
            "free-data-ui.js",
            "command-centre.js",
        }
        self.assertTrue(required_scripts.issubset(position), required_scripts - set(position))
        expected_order = (
            ("data.js", "app.js"),
            ("command-centre-data.js", "command-centre.js"),
            ("intelligence-data.js", "intelligence-app.js"),
            ("politicians.js", "intelligence-app.js"),
            ("free-data.js", "free-data-ui.js"),
        )
        for provider, consumer in expected_order:
            with self.subTest(provider=provider, consumer=consumer):
                self.assertLess(position[provider], position[consumer])

    def test_every_navigation_route_has_a_matching_view(self) -> None:
        missing = self.parser.nav_routes - self.parser.views
        self.assertEqual(missing, set())

    def test_initial_hash_is_captured_before_external_scripts(self) -> None:
        inline = self.html.find("window.__marketInitialHash")
        first_external = re.search(r'<script\s+src="', self.html)
        self.assertGreaterEqual(inline, 0)
        self.assertIsNotNone(first_external)
        self.assertLess(inline, first_external.start())


if __name__ == "__main__":
    unittest.main()
