import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import state_store


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp_dir.name) / "test_state.json"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_default_state(self):
        s = state_store.default_state()
        self.assertIn("users", s)
        self.assertIn("subscribers", s)
        self.assertIn("seen_news_hashes", s)

    def test_local_json_save_and_load(self):
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            data = {"subscribers": [123], "seen_news_hashes": ["hash1"], "users": {"123": {"k": "v"}}}
            state_store.save(self.path, data)
            loaded = state_store.load(self.path)
            self.assertEqual(loaded["users"]["123"]["k"], "v")
            self.assertEqual(loaded["subscribers"], [123])

    def test_unreachable_postgres_fallback_on_load(self):
        # Even with a broken DATABASE_URL, load must not crash and must fallback to local JSON
        fake_db = "postgresql://user:pass@127.0.0.1:54329/fake_db"
        with patch.dict(os.environ, {"DATABASE_URL": fake_db}, clear=False), \
             patch("psycopg.connect", side_effect=Exception("Connection refused")):
            data = {"subscribers": [999], "seen_news_hashes": [], "users": {"999": {"name": "Mert"}}}
            self.path.write_text(state_store.json.dumps(data), encoding="utf-8")

            loaded = state_store.load(self.path)
            self.assertEqual(loaded["users"]["999"]["name"], "Mert")

    def test_unreachable_postgres_fallback_on_save(self):
        # Even with a broken DATABASE_URL, save must not crash and must write to local JSON
        fake_db = "postgresql://user:pass@127.0.0.1:54329/fake_db"
        with patch.dict(os.environ, {"DATABASE_URL": fake_db}, clear=False), \
             patch("psycopg.connect", side_effect=Exception("Connection refused")):
            data = {"subscribers": [555], "seen_news_hashes": [], "users": {"555": {"city": "Austin"}}}
            state_store.save(self.path, data)

            self.assertTrue(self.path.exists())
            loaded = state_store.json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["users"]["555"]["city"], "Austin")

    def test_get_storage_status_local(self):
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            status = state_store.get_storage_status()
            self.assertFalse(status["postgres_configured"])
            self.assertEqual(status["active_backend"], "local_json")


if __name__ == "__main__":
    unittest.main()
