"""Tests for Smart User Profile Memory in GreenCard27."""
import unittest
from profile_manager import (
    extract_profile_facts,
    update_user_facts,
    set_profile_field,
    clear_profile_facts,
    format_profile_view,
    format_profile_for_prompt,
    normalize_field_name,
)


class ProfileMemoryTests(unittest.TestCase):
    def test_natural_language_extraction_full(self):
        text = (
            "Ben 32 yaşında kıdemli yazılımcıyım, eşim hemşire, 1 çocuğumuz var, "
            "20 bin dolar birikimimiz var ve Texas veya Washington düşünüyoruz."
        )
        facts = extract_profile_facts(text)
        self.assertIn("Kıdemli Yazılımcı", facts.get("meslek", ""))
        self.assertIn("Evli", facts.get("medeni_durum", ""))
        self.assertIn("Hemşire", facts.get("medeni_durum", ""))
        self.assertIn("1 Çocuk", facts.get("medeni_durum", ""))
        self.assertIn("20 bin dolar", facts.get("butce", ""))
        self.assertTrue("Texas" in facts.get("hedef_lokasyon", "") or "Washington" in facts.get("hedef_lokasyon", ""))

    def test_partial_sentences_extraction(self):
        # Meslek
        f1 = extract_profile_facts("Ben veri analisti olarak çalışıyorum.")
        self.assertEqual(f1.get("meslek"), "Veri Analisti")

        # Bütçe
        f2 = extract_profile_facts("Yaklaşık 15.000$ bütçemiz var.")
        self.assertIn("15.000$", f2.get("butce", ""))

        # Eğitim ve İngilizce
        f3 = extract_profile_facts("Lisans mezunuyum ve ingilizcem B2 seviyesinde.")
        self.assertEqual(f3.get("egitim"), "Lisans")
        self.assertEqual(f3.get("ingilizce"), "B2")

        # Hedef şehir
        f4 = extract_profile_facts("Austin veya Seattle tarafına yerleşmek istiyoruz.")
        self.assertTrue("Austin" in f4.get("hedef_lokasyon", ""))
        self.assertTrue("Seattle" in f4.get("hedef_lokasyon", ""))

    def test_alias_normalization(self):
        self.assertEqual(normalize_field_name("iş"), "meslek")
        self.assertEqual(normalize_field_name("bütçe"), "butce")
        self.assertEqual(normalize_field_name("eyalet"), "hedef_lokasyon")
        self.assertEqual(normalize_field_name("şehir"), "hedef_lokasyon")
        self.assertEqual(normalize_field_name("aile"), "medeni_durum")
        self.assertEqual(normalize_field_name("unknown_foo"), None)

    def test_manual_field_update(self):
        facts = {}
        res = set_profile_field(facts, "eyalet", "Austin, Texas")
        self.assertEqual(res, "hedef_lokasyon")
        self.assertEqual(facts["hedef_lokasyon"], "Austin, Texas")

        res2 = set_profile_field(facts, "butce", "25.000 USD")
        self.assertEqual(res2, "butce")
        self.assertEqual(facts["butce"], "25.000 USD")

    def test_update_and_clear_facts(self):
        existing = {"meslek": "Yazılımcı"}
        changed = update_user_facts(existing, {"butce": "10 bin dolar"})
        self.assertTrue(changed)
        self.assertEqual(existing["meslek"], "Yazılımcı")
        self.assertEqual(existing["butce"], "10 bin dolar")

        profile = {"user_facts": existing}
        clear_profile_facts(profile)
        self.assertEqual(profile["user_facts"], {})

    def test_format_profile_view(self):
        facts = {
            "meslek": "Yazılım Mühendisi",
            "butce": "20.000$",
            "hedef_lokasyon": "Texas (Austin)",
        }
        view = format_profile_view(facts)
        self.assertIn("Yazılım Mühendisi", view)
        self.assertIn("20.000$", view)
        self.assertIn("Texas (Austin)", view)
        self.assertIn("/profil_temizle", view)

    def test_format_profile_for_prompt(self):
        facts = {
            "meslek": "Yazılım Mühendisi",
            "butce": "20.000$",
            "hedef_lokasyon": "Texas (Austin)",
        }
        prompt_block = format_profile_for_prompt(facts)
        self.assertIn("Yazılım Mühendisi", prompt_block)
        self.assertIn("20.000$", prompt_block)
        self.assertIn("Texas (Austin)", prompt_block)


if __name__ == "__main__":
    unittest.main()
