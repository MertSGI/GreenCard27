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
             patch("greencard_telegram_bot.genai.Client"), \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            reply = bot.answer_user_question("Yazılımcı olarak Teksas mı Kaliforniya mı daha avantajlı?", self.profile)
            self.assertIn("Kaliforniya", reply)
            
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
        """Multi-turn memory is passed in prompt to Gemini with continuity instructions."""
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
            self.assertIn("KRİTİK BAĞLAM VE DİYALOG TALİMATLARI", contents)
            self.assertIn("BAĞLAMI VE ZAMİRLERİ KESİNLİKLE ÇÖZÜMLE", contents)

    def test_format_chat_history(self):
        history = [
            {"role": "user", "text": "Soru 1"},
            {"role": "assistant", "text": "Cevap 1"},
        ]
        formatted = bot.format_chat_history(history)
        self.assertIn("Kullanıcı: Soru 1", formatted)
        self.assertIn("Koç: Cevap 1", formatted)

    def test_record_chat_turn(self):
        profile = {"chat_history": []}
        bot.record_chat_turn(profile, "Merhaba", "Selam, nasıl yardımcı olabilirim?")
        self.assertEqual(len(profile["chat_history"]), 2)
        self.assertEqual(profile["chat_history"][0]["role"], "user")
        self.assertEqual(profile["chat_history"][0]["text"], "Merhaba")
        self.assertEqual(profile["chat_history"][1]["role"], "assistant")
        self.assertEqual(profile["chat_history"][1]["text"], "Selam, nasıl yardımcı olabilirim?")

    def test_follow_up_progress_detection_from_history(self):
        """Short follow-ups like 'onu yaptım sıradaki ne?' detect progress context."""
        history = [
            {"role": "user", "text": "Checklist'imde hangi adım var?"},
            {"role": "assistant", "text": "1. adım pasaport geçerliliği."},
        ]
        self.assertTrue(bot.is_personal_progress_query("Onu yaptım, sıradaki ne?", history))
        self.assertTrue(bot.is_personal_progress_query("Tamam bitti, şimdi ne yapıyoruz?", history))

    def test_follow_up_gc_detection_from_history(self):
        """Short follow-ups like 'peki bu durum ertelendi mi?' detect GC context."""
        history = [
            {"role": "user", "text": "DV-2027 Red Eagle Law davası ne durumda?"},
            {"role": "assistant", "text": "Mahkeme tedbir kararı verdi."},
        ]
        self.assertTrue(bot.is_gc_process_query("Peki bu durum başvuru tarihini etkiler mi?", history))

    def test_user_profile_facts_injected_in_prompt(self):
        """When user has stored profile facts, they are injected into Gemini prompt."""
        self.profile["user_facts"] = {
            "meslek": "Kıdemli Yazılımcı",
            "butce": "20.000$",
            "hedef_lokasyon": "Austin, Texas",
        }
        mock_response = MagicMock(text="Austin'de yazılımcı olarak 20 bin dolar birikimle ilk 3 ay rahat yönetilir.")
        with patch.object(bot, "HAS_GENAI", True), \
             patch.object(bot, "GEMINI_API_KEY", "fake_key"), \
             patch("greencard_telegram_bot.genai.Client"), \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            reply = bot.answer_user_question("Oraya gidince ilk ay ev kiralamak zor mu?", self.profile)
            self.assertIn("Austin", reply)
            
            call_kwargs = mock_gen.call_args[1]
            contents = call_kwargs["contents"]
            self.assertIn("KULLANICININ BİLİNEN KİŞİSEL PROFİLİ", contents)
            self.assertIn("Kıdemli Yazılımcı", contents)
            self.assertIn("20.000$", contents)
            self.assertIn("Austin, Texas", contents)

    def test_empty_user_profile_facts_not_injected(self):
        """When user facts are empty, profile block is omitted from prompt."""
        self.profile["user_facts"] = {}
        mock_response = MagicMock(text="Genel tavsiyem...")
        with patch.object(bot, "HAS_GENAI", True), \
             patch.object(bot, "GEMINI_API_KEY", "fake_key"), \
             patch("greencard_telegram_bot.genai.Client"), \
             patch("greencard_telegram_bot.generate_with_fallback", return_value=(mock_response, "gemini-3.5-flash-lite")) as mock_gen:
            
            bot.answer_user_question("Genel tavsiyen nedir?", self.profile)
            call_kwargs = mock_gen.call_args[1]
            contents = call_kwargs["contents"]
            self.assertNotIn("KULLANICININ BİLİNEN KİŞİSEL PROFİLİ", contents)


if __name__ == "__main__":
    unittest.main()
