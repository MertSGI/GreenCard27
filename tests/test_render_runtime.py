import os
import unittest
from unittest.mock import patch

from render_runtime import BotWebhookRuntime, resolve_base_url, webhook_identity


class FakeApp:
    running = True


class WebhookTests(unittest.TestCase):
    def test_token_not_in_path_or_secret(self):
        token = "1234:FAKE_SECRET"
        path, secret = webhook_identity(token)
        self.assertTrue(path.startswith("/tg/"))
        self.assertNotIn(token, path + secret)
        self.assertEqual(webhook_identity(token), (path, secret))

    def test_new_token_changes_webhook(self):
        self.assertNotEqual(webhook_identity("a:b"), webhook_identity("a:c"))

    def test_render_environment_url(self):
        with patch.dict(os.environ, {"RENDER_EXTERNAL_URL": "https://greencard27.onrender.com"}, clear=True):
            self.assertEqual(resolve_base_url(), "https://greencard27.onrender.com")

    def test_non_https_rejected(self):
        with patch.dict(os.environ, {"WEBHOOK_BASE_URL": "http://127.0.0.1:10000"}, clear=True):
            with self.assertRaises(RuntimeError):
                resolve_base_url()

    def test_ready_after_register(self):
        state = BotWebhookRuntime(FakeApp(), "1:example", "https://example.onrender.com")
        self.assertEqual(state.health_payload()["status"], "starting")
        state.ready = True
        self.assertEqual(state.health_payload()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
