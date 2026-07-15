from __future__ import annotations

import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.scripts.append(str(values["src"]))


class CoreModuleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = (SITE / "index.html").read_text(encoding="utf-8")
        cls.parser = ScriptParser()
        cls.parser.feed(cls.index)

    def test_core_runtime_behaviour_in_node(self) -> None:
        subprocess.run(
            ["node", "tests/js/core-runtime.test.js"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_core_scripts_load_after_data_and_before_renderers(self) -> None:
        position = {name: index for index, name in enumerate(self.parser.scripts)}
        core_scripts = [
            "core/format.js",
            "core/status.js",
            "core/store.js",
            "core/adapters.js",
            "core/router.js",
        ]
        self.assertTrue(set(core_scripts).issubset(position), set(core_scripts) - set(position))
        self.assertLess(position["energy-expansion.js"], position["core/adapters.js"])
        self.assertLess(position["core/format.js"], position["core/status.js"])
        self.assertLess(position["core/status.js"], position["core/store.js"])
        self.assertLess(position["core/store.js"], position["core/adapters.js"])
        self.assertLess(position["core/adapters.js"], position["core/router.js"])
        for consumer in ("app.js", "intelligence-app.js", "quiver-patterns.js", "free-data-ui.js", "energy-data-ui.js", "command-centre.js", "shell.js"):
            with self.subTest(consumer=consumer):
                self.assertLess(position["core/router.js"], position[consumer])

    def test_existing_renderers_read_through_adapters(self) -> None:
        files = (
            "app.js",
            "intelligence-app.js",
            "command-centre.js",
            "free-data-ui.js",
            "energy-data-ui.js",
            "quiver-patterns.js",
            "scenario-ui.js",
            "cot-chart.js",
        )
        for name in files:
            with self.subTest(file=name):
                text = (SITE / name).read_text(encoding="utf-8")
                self.assertIn("MarketBriefCore", text)
                self.assertIn("core.adapters", text)

    def test_shared_router_owns_initial_hash_and_feature_routes(self) -> None:
        shell = (SITE / "shell.js").read_text(encoding="utf-8")
        app = (SITE / "app.js").read_text(encoding="utf-8")
        intelligence = (SITE / "intelligence-app.js").read_text(encoding="utf-8")
        free_data = (SITE / "free-data-ui.js").read_text(encoding="utf-8")
        command = (SITE / "command-centre.js").read_text(encoding="utf-8")
        scenario = (SITE / "scenario-ui.js").read_text(encoding="utf-8")
        market_watch = (
            SITE / "features" / "market-watch" / "market-watch-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn("router.start(window.__marketInitialHash", shell)
        self.assertIn("router.registerPattern('product-detail'", app)
        for route in ("news", "trackers"):
            self.assertIn(f"router.register('{route}'", intelligence)
        for route in ("cot", "rates", "events"):
            self.assertIn(route, free_data)
        self.assertIn("router.register('home'", command)
        self.assertIn("router.register('scenarios'", scenario)
        self.assertIn("current?.path === 'equities'", market_watch)
        self.assertIn("source: 'market-watch-ready'", market_watch)
        self.assertIn("host();", market_watch)
        self.assertIn("equities: ['Equity Tape'", shell)

    def test_legacy_globals_are_wrapped_not_removed(self) -> None:
        adapters = (SITE / "core" / "adapters.js").read_text(encoding="utf-8")
        self.assertIn("typeof fallback !== 'undefined'", adapters)
        self.assertIn("window.freeMarketData", adapters)
        self.assertIn("window.marketResearchData", adapters)
        self.assertIn("window.scenarioAssets", adapters)
        self.assertNotIn("delete window", adapters)


if __name__ == "__main__":
    unittest.main()
