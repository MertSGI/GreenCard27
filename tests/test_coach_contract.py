"""Smoke-check common user-facing command and source contract."""
import unittest
from unittest.mock import patch
import greencard_telegram_bot as bot


class ContentSafetyTests(unittest.TestCase):
    def test_guides_have_five_phases(self):
        self.assertEqual(len(bot.PHASES_GUIDE), 5)
    def test_no_guaranteed_december_result(self):
        combined="\n".join(bot.PHASES_GUIDE.values())
        self.assertNotIn("3 Aralık 2026", combined)
        self.assertIn("Entrant Status Check", combined)
    def test_personal_coach_commands_are_present(self):
        self.assertTrue(callable(bot.cmd_bugun))
        self.assertTrue(callable(bot.cmd_bildirim_test))
        self.assertTrue(callable(bot.cmd_id))
    def test_daily_digest_is_actionable(self):
        sample={"checklist":{}, "ds260":{}}
        body=bot.generate_daily_coaching_brief(sample)
        self.assertIn("BUGÜNKÜ SOMUT ADIMLAR",body)
        self.assertIn("/checklist",body)


if __name__=="__main__":
    unittest.main()
