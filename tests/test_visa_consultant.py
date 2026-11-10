"""Unit tests for Visa Consultant (Case Transfer, 360° US Visas, DS-260 3-Eyes Audit)."""
import unittest
from visa_consultant import (
    analyze_transfer_and_build_letter,
    analyze_all_us_visas,
    audit_ds260_consistency,
    generate_proactive_case_emails,
    build_proactive_action_plan,
)
from profile_manager import extract_profile_facts
import greencard_telegram_bot as bot


class VisaConsultantTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "checklist": {"passport_valid": True},
            "ds260": {
                "full_name": "MERT OZCELIKBAS",
                "birth_info": "1994-05-10 Istanbul",
                "passport_no": "U12345678 10.10.2032",
                "marital_dependents": "Married, 1 child",
                "social_media": "LinkedIn: mertoz, X: mertoz",
            },
            "user_facts": {
                "meslek": "Kıdemli Yazılım Mühendisi",
                "egitim": "Yüksek Lisans",
                "butce": "90.000$",
                "medeni_durum": "Evli, 1 Çocuk",
                "ingilizce": "C1",
                "case_number": "2027EU00018500",
            },
        }

    def test_transfer_policy_overview_when_empty(self):
        out = analyze_transfer_and_build_letter("", self.profile)
        self.assertIn("Dosya Taşıma (Case Transfer)", out)
        self.assertIn("KCCDV@state.gov", out)
        self.assertIn("2NL", out)
        self.assertIn("ustraveldocs.com", out)

    def test_transfer_with_residency_generates_letter(self):
        out = analyze_transfer_and_build_letter(
            "Viyana oturum iznim var, dosyamı Avusturya'ya taşımak istiyorum",
            self.profile,
        )
        self.assertIn("Güçlü Transfer Zemini", out)
        self.assertIn("2027EU00018500", out)
        self.assertIn("MERT OZCELIKBAS", out)
        self.assertIn("Case Transfer Request", out)

    def test_transfer_tourist_warns_risk(self):
        out = analyze_transfer_and_build_letter(
            "Turist olarak Gürcistan üzerinden hızlı sıraya taşıyabilir miyim?",
            self.profile,
        )
        self.assertIn("Kritik Risk Uyarısı", out)

    def test_unlock_letter_generation(self):
        out = analyze_transfer_and_build_letter("DS-260 kilidi unlock açtırmak istiyorum", self.profile)
        self.assertIn("DS-260 Unlock Request", out)
        self.assertIn("Sign and Submit", out)

    def test_expedited_appointment_generation(self):
        out = analyze_transfer_and_build_letter("F-1 okul başlangıcı için acil randevu", self.profile)
        self.assertIn("Expedited Visa Appointment", out)
        self.assertIn("DS-160", out)

    def test_transfer_with_ai_callable(self):
        captured = {}

        def fake_ai(prompt: str) -> str:
            captured["prompt"] = prompt
            return "Özel danışman notu: Oturum kartınızı PDF yerine JPEG/PDF net tarama ile ekleyin."

        out = analyze_transfer_and_build_letter(
            "Almanya Blue Card oturumum var",
            self.profile,
            use_ai=True,
            ai_callable=fake_ai,
        )
        self.assertIn("2027EU00018500", captured["prompt"])
        self.assertIn("Özel danışman notu", out)

    def test_analyze_all_us_visas_high_budget_stem(self):
        report = analyze_all_us_visas(self.profile)
        self.assertIn("EB-2 NIW", report)
        self.assertIn("Yüksek Uygunluk", report)
        self.assertIn("Güçlü Finansal Uygunluk", report)
        self.assertIn("214(b)", report)

    def test_analyze_all_us_visas_low_budget(self):
        low_prof = {
            "user_facts": {
                "meslek": "Grafiker",
                "egitim": "Lise",
                "butce": "12.000$",
                "ingilizce": "Orta",
            }
        }
        report = analyze_all_us_visas(low_prof)
        self.assertIn("Düşük Sermaye Uygunluğu", report)
        self.assertIn("DV Lottery", report)

    def test_audit_ds260_detects_turkish_chars_and_marital_conflict(self):
        bad_profile = {
            "checklist": {"passport_valid": False},
            "ds260": {
                "full_name": "Mert Özçelikbaş",
                "passport_no": "U12345678",
                "marital_dependents": "Bekar",
                "address_history": "Istanbul",
                "social_media": "",
            },
            "user_facts": {"medeni_durum": "Evli, 1 Çocuk"},
        }
        report = audit_ds260_consistency(bad_profile, bot.DS260_FIELDS)
        self.assertIn("Türkçe Karakter Riski", report)
        self.assertIn("Kritik Çapraz Çelişki", report)
        self.assertIn("Sosyal Medya Alanı Boş", report)
        self.assertIn("Checklist Uyumsuzluğu", report)

    def test_audit_ds260_clean_with_ai(self):
        def fake_ai(prompt: str) -> str:
            return "Tarihler tutarlı görünüyor; sosyal medya kullanıcı adları güncel."

        report = audit_ds260_consistency(self.profile, bot.DS260_FIELDS, ai_callable=fake_ai)
        self.assertIn("Pasaport adı İngilizce karakter formatına uygun", report)
        self.assertIn("AI Konsolosluk Ön İncelemesi", report)
        self.assertIn("Tarihler tutarlı görünüyor", report)

    def test_generate_proactive_case_emails_suite(self):
        kcc_mail = generate_proactive_case_emails("kcc_status", self.profile)
        self.assertIn("KCCDV@state.gov", kcc_mail)
        self.assertIn("2027EU00018500", kcc_mail)
        self.assertIn("MERT OZCELIKBAS", kcc_mail)

        urgent_mail = generate_proactive_case_emails("urgent_embassy", self.profile)
        self.assertIn("September 30", urgent_mail)
        self.assertIn("URGENT: Fiscal Year Expiration Risk", urgent_mail)

        ap_mail = generate_proactive_case_emails("ap_221g", self.profile)
        self.assertIn("221(g) Administrative Processing Follow-Up", ap_mail)

        pc_letter = generate_proactive_case_emails("public_charge", self.profile)
        self.assertIn("MEMORANDUM OF FINANCIAL SELF-SUFFICIENCY", pc_letter)
        self.assertIn("Kıdemli Yazılım Mühendisi", pc_letter)

    def test_build_proactive_action_plan_high_case_and_stem(self):
        high_prof = {
            "checklist": {"passport_valid": True},
            "ds260": {"full_name": "MERT OZCELIKBAS"},
            "user_facts": {
                "meslek": "Yazılım Mühendisi",
                "egitim": "Yüksek Lisans",
                "butce": "14.000$",
                "medeni_durum": "Evli, 1 Çocuk",
                "case_number": "2027EU00031500",
            },
        }
        plan = build_proactive_action_plan(high_prof)
        self.assertIn("SENİN YERİNE DÜŞÜNDÜM: 360° PROAKTİF STRATEJİ", plan)
        self.assertIn("2027EU00031500", plan)
        self.assertIn("Yüksek Sıra / Dar Takvim Hamlesi", plan)
        self.assertIn("221(g) Kalkanı", plan)
        self.assertIn("EB-2 NIW", plan)
        self.assertIn("Public Charge", plan)
        self.assertIn("KCCDV@state.gov", plan)

    def test_shorthand_case_extraction_and_bot_proactive_fallback(self):
        extracted = extract_profile_facts("Sıra numaram EU29500 çıktı ve süre kısıtlı, ne yapmalıyım?")
        self.assertEqual(extracted.get("case_number"), "2027EU00029500")
        self.assertTrue(bot.is_case_or_kcc_action_query("Sıra numaram EU29500 çıktı, KCC'ye mail atalım mı?"))


if __name__ == "__main__":
    unittest.main()
