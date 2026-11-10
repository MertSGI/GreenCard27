import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import coach_core
import state_store

ITEMS = [("a", "A görev"), ("b", "B görev")]


class CoachTests(unittest.TestCase):
    def test_daily_once_per_user(self):
        self.assertTrue(coach_core.due({}, "2026-10-26", 9))
        self.assertFalse(coach_core.due({"last_daily_digest": "2026-10-26"}, "2026-10-26", 9))
        self.assertFalse(coach_core.due({}, "2026-10-26", 8))

    def test_brief_next_action(self):
        txt = coach_core.digest({"checklist": {"a": True}}, ITEMS, datetime(2026, 10, 26))
        self.assertIn("B görev", txt)
        self.assertNotIn("3 Aralık", txt)

    def test_no_fake_first_news_alert(self):
        news = [{"id": "a", "title": "x", "link": "https://example.com"}]
        self.assertEqual(coach_core.new_headlines(news, []), [])
        self.assertEqual(coach_core.new_headlines(news, ["b"]), news)

    def test_local_state(self):
        with TemporaryDirectory() as td:
            with patch.dict("os.environ", {"DATABASE_URL": ""}):
                p = Path(td) / "state.json"
                state_store.save(p, {"users": {"1": {"test": 1}}})
                self.assertEqual(state_store.load(p)["users"]["1"]["test"], 1)

    def test_analyze_daily_news_scenarios_limits_to_two_and_reasons(self):
        headlines = [
            {
                "id": "1",
                "title": "Ninth Circuit Grants Emergency Stay in Red Eagle Law Case",
                "source": "Court News",
                "link": "https://example.com/1",
                "summary": "Appeal stay keeps registration closed for now.",
            },
            {
                "id": "2",
                "title": "KCC Restricts Third-Country Case Transfer Without Residency",
                "source": "Visa Desk",
                "link": "https://example.com/2",
                "summary": "Ankara backlog pushes applicants to seek embassy transfers.",
            },
            {
                "id": "3",
                "title": "Should Not Be Included Third Headline",
                "source": "Other",
                "link": "https://example.com/3",
            },
        ]
        profile = {"user_facts": {"meslek": "Yazılım Mühendisi", "hedef_lokasyon": "Texas"}}
        report = coach_core.analyze_daily_news_scenarios(headlines, profile)
        self.assertIn("Ninth Circuit Grants Emergency Stay", report)
        self.assertIn("KCC Restricts Third-Country", report)
        self.assertNotIn("Should Not Be Included Third Headline", report)
        self.assertIn("Bu Şekilde Olabilir", report)
        self.assertIn("Böyle Hazır Olmalıyız", report)
        self.assertIn("Yazılım Mühendisi", report)

    def test_analyze_daily_news_scenarios_with_ai_callable(self):
        headlines = [
            {"id": "1", "title": "News One", "source": "S1", "link": "https://example.com/1"},
            {"id": "2", "title": "News Two", "source": "S2", "link": "https://example.com/2"},
        ]
        captured = {}

        def fake_ai(prompt: str) -> str:
            captured["prompt"] = prompt
            return "🔮 *Bu Şekilde Olabilir:* Portal aniden açılabilir.\n🛡️ *Böyle Hazır Olmalıyız:* Evrakları hazırlayalım."

        out = coach_core.analyze_daily_news_scenarios(headlines, {"user_facts": {}}, ai_callable=fake_ai)
        self.assertIn("News One", captured["prompt"])
        self.assertIn("News Two", captured["prompt"])
        self.assertIn("Portal aniden açılabilir", out)

    def test_digest_includes_two_news_scenario_block(self):
        headlines = [
            {"id": "1", "title": "Ninth Circuit Appeal Update", "source": "S1", "link": "https://example.com/1"},
            {"id": "2", "title": "Consulate Transfer Guidance", "source": "S2", "link": "https://example.com/2"},
        ]
        txt = coach_core.digest({"checklist": {"a": True}}, ITEMS, datetime(2026, 11, 10), headlines=headlines)
        self.assertIn("B görev", txt)
        self.assertIn("GÜNÜN 2 KRİTİK HABERİ", txt)
        self.assertIn("Bu Şekilde Olabilir", txt)


if __name__ == "__main__":
    unittest.main()
