import unittest
from unittest.mock import patch, MagicMock
import greencard_telegram_bot as bot


class UnrestrictedCoachTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "checklist": {"passport_valid": False, "passport_scan": False},
            "ds260": {"full_name": ""},
            "chat_history": [],
        }

    def test_general_question_does_not_inject_checklist_nag(self):
        """General questions (cities, career, etc.) should not burden the prompt with checklist items."""
        mock_response = MagicMock(text="Kaliforniya ve Teksas teknoloji kariyerinde iki güçlü alternatiftir.")
        with patch.object(bot, "HAS_GENAI", True), \
             patch.object(bot, "GEMINI_API_KEY", "fake_key"), \
             patch("greencard_telegram_bot.genai.Client") as mock_client_cls, \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            reply = bot.answer_user_question("Yazılımcı olarak Teksas mı Kaliforniya mı daha avantajlı?", self.profile)
            self.assertIn("Kaliforniya", reply)
            
            # Check prompt content sent to Gemini
            call_kwargs = mock_gen.call_args[1]
            contents = call_kwargs["contents"]
            self.assertNotIn("KULLANICININ HAZIRLIK PROFİLİ", contents)
            self.assertNotIn("Tamamlanan Adımlar", contents)
            self.assertIn("Yazılımcı olarak Teksas mı Kaliforniya mı", contents)

    def test_progress_question_injects_checklist(self):
        """When user asks about checklist or progress, profile context is included."""
        mock_response = MagicMock(text="Checklist'inizde şu anda pasaport hazırlığı bekleniyor.")
        with patch.object(bot, "HAS_GENAI", True), \
             patch.object(bot, "GEMINI_API_KEY", "fake_key"), \
             patch("greencard_telegram_bot.genai.Client"), \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            reply = bot.answer_user_question("Checklist durumum nedir, sırada ne yapmalıyım?", self.profile)
            self.assertIn("Checklist", reply)
            
            call_kwargs = mock_gen.call_args[1]
            contents = call_kwargs["contents"]
            self.assertIn("KULLANICININ HAZIRLIK PROFİLİ", contents)
            self.assertIn("Tamamlanan Adımlar", contents)

    def test_chat_history_injected_in_prompt(self):
        """Multi-turn memory is passed in prompt to Gemini."""
        self.profile["chat_history"] = [
            {"role": "user", "text": "Austin hakkında ne düşünüyorsun?"},
            {"role": "assistant", "text": "Austin teknoloji şirketleri açısından hızla büyüyen bir merkez."},
        ]
        mock_response = MagicMock(text="Dallas daha kurumsal finans ve ticaret odaklıdır.")
        with patch.object(bot, "HAS_GENAI", True), \
             patch.object(bot, "GEMINI_API_KEY", "fake_key"), \
             patch("greencard_telegram_bot.genai.Client"), \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            reply = bot.answer_user_question("Peki ya Dallas?", self.profile)
            self.assertIn("Dallas", reply)
            
            call_kwargs = mock_gen.call_args[1]
            contents = call_kwargs["contents"]
            self.assertIn("ÖNCEKİ SOHBET GEÇMİŞİ", contents)
            self.assertIn("Austin hakkında ne düşünüyorsun?", contents)

    def test_format_chat_history(self):
        history = [
            {"role": "user", "text": "Soru 1"},
            {"role": "assistant", "text": "Cevap 1"},
        ]
        formatted = bot.format_chat_history(history)
        self.assertIn("Kullanıcı: Soru 1", formatted)
        self.assertIn("Koç: Cevap 1", formatted)


if __name__ == "__main__":
    unittest.main()
