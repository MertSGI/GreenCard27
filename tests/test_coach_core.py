import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import coach_core
import state_store

ITEMS=[("a","A görev"),("b","B görev")]
class CoachTests(unittest.TestCase):
    def test_daily_once_per_user(self):
        self.assertTrue(coach_core.due({}, "2026-10-26", 9))
        self.assertFalse(coach_core.due({"last_daily_digest":"2026-10-26"},"2026-10-26",9))
        self.assertFalse(coach_core.due({}, "2026-10-26",8))
    def test_brief_next_action(self):
        txt=coach_core.digest({"checklist":{"a":True}},ITEMS,datetime(2026,10,26))
        self.assertIn("B görev",txt)
        self.assertNotIn("3 Aralık",txt)
    def test_no_fake_first_news_alert(self):
        news=[{"id":"a","title":"x","link":"https://example.com"}]
        self.assertEqual(coach_core.new_headlines(news,[]),[])
        self.assertEqual(coach_core.new_headlines(news,["b"]),news)
    def test_local_state(self):
        with TemporaryDirectory() as td:
            with patch.dict("os.environ",{"DATABASE_URL":""}):
                p=Path(td)/"state.json"
                state_store.save(p,{"users":{"1":{"test":1}}})
                self.assertEqual(state_store.load(p)["users"]["1"]["test"],1)

if __name__=="__main__":
    unittest.main()
