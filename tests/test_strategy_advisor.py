"""Unit tests for Strategy Advisor (Relocation, Case, Audit, Visas, Glossary)."""
import unittest
from strategy_advisor import (
    calculate_relocation_budget,
    format_runway_report,
    compare_states,
    get_state_profile,
    get_state_keys,
    analyze_case_number,
    format_case_analysis,
    generate_readiness_audit,
    format_audit_report,
    get_visa_routes_guide,
    lookup_glossary,
    parse_numeric_budget,
)


class StrategyAdvisorTests(unittest.TestCase):
    def test_parse_numeric_budget(self):
        self.assertEqual(parse_numeric_budget("25000"), 25000.0)
        self.assertEqual(parse_numeric_budget("20.000$"), 20000.0)
        self.assertEqual(parse_numeric_budget("15 bin dolar"), 15000.0)
        self.assertEqual(parse_numeric_budget("30k USD"), 30000.0)
        self.assertEqual(parse_numeric_budget(40000), 40000.0)
        self.assertEqual(parse_numeric_budget(""), 0.0)

    def test_calculate_relocation_budget_texas_single(self):
        calc = calculate_relocation_budget("25000$", "texas", is_family=False)
        self.assertEqual(calc["budget"], 25000.0)
        self.assertIn("Texas", calc["state_name"])
        self.assertGreater(calc["total_startup_cost"], 5000)
        self.assertGreater(calc["runway_months"], 2.0)
        self.assertIn("Güvenli", calc["risk_level"])
        report = format_runway_report(calc)
        self.assertIn("Texas", report)
        self.assertIn("Runway", report)
        self.assertIn("Public Charge", report)

    def test_calculate_relocation_budget_family_low(self):
        calc = calculate_relocation_budget("10000$", "california", is_family=True, family_members=3)
        self.assertIn("California", calc["state_name"])
        self.assertIn("Yüksek Risk", calc["risk_level"])
        self.assertLess(calc["runway_months"], 1.0)

    def test_state_comparison(self):
        text = compare_states("texas", "california")
        self.assertIn("Texas", text)
        self.assertIn("California", text)
        self.assertIn("Eyalet Gelir Vergisi", text)
        self.assertIn("Yazılım", text)

    def test_get_state_profile_valid_and_invalid(self):
        tx = get_state_profile("texas")
        self.assertIsNotNone(tx)
        self.assertTrue("%0" in tx["income_tax"] or "0%" in tx["income_tax"])
        self.assertIsNone(get_state_profile("invalid_state_xyz"))

    def test_analyze_case_number_valid(self):
        res1 = analyze_case_number("2027EU00014250")
        self.assertTrue(res1["valid"])
        self.assertEqual(res1["year"], "2027")
        self.assertEqual(res1["region_code"], "EU")
        self.assertEqual(res1["rank"], 14250)
        self.assertIn("Orta Numara", res1["tier"])
        report1 = format_case_analysis(res1)
        self.assertIn("2027EU00014250", report1)
        self.assertIn("Avrupa", report1)

    def test_analyze_case_number_low_and_high(self):
        res_low = analyze_case_number("2027EU00002500")
        self.assertIn("Altın Sıra", res_low["tier"])
        res_high = analyze_case_number("2027EU00045000")
        self.assertIn("Çok Yüksek Numara", res_high["tier"])
        self.assertEqual(len(res_high["scenarios"]), 3)
        self.assertGreaterEqual(len(res_high["immediate_actions"]), 3)
        self.assertIn("KCCDV@state.gov", res_high["kcc_email"]["to"])
        self.assertIn("Urgent Case Status", res_high["kcc_email"]["subject"])

    def test_analyze_case_number_shorthand_and_proactive_kcc_draft(self):
        prof = {
            "ds260": {
                "full_name": "MERT OZCELIKBAS",
                "birth_info": "1994-05-10",
            },
            "user_facts": {},
        }
        res_short = analyze_case_number("EU28500", prof)
        self.assertTrue(res_short["valid"])
        self.assertEqual(res_short["raw"], "2027EU00028500")
        self.assertEqual(res_short["rank"], 28500)
        formatted = format_case_analysis(res_short, prof)
        self.assertIn("SENİN YERİNE DÜŞÜNDÜM: OLASI SENARYOLAR", formatted)
        self.assertIn("onlara şu şekilde söyleyelim", formatted.lower())
        self.assertIn("KCCDV@state.gov", formatted)
        self.assertIn("MERT OZCELIKBAS", formatted)

    def test_analyze_case_number_invalid(self):
        res = analyze_case_number("invalid_case_123")
        self.assertFalse(res["valid"])
        self.assertIn("Geçerli bir Case Number", format_case_analysis(res))

    def test_readiness_audit_empty(self):
        empty_profile = {"checklist": {}, "ds260": {}, "user_facts": {}}
        audit = generate_readiness_audit(empty_profile)
        self.assertLess(audit["score"], 50)
        self.assertIn("Başlangıç", audit["badge"])
        self.assertTrue(len(audit["red_flags"]) > 0)
        self.assertTrue(len(audit["priorities"]) > 0)
        report = format_audit_report(audit)
        self.assertIn("Green Card Hazırlık", report)
        self.assertIn("Puanı", report)

    def test_readiness_audit_full(self):
        full_profile = {
            "checklist": {
                "passport_valid": True,
                "passport_scan": True,
                "photo_taken": True,
                "photo_tested": True,
                "vaccine_check": True,
                "mock_interview": True,
            },
            "ds260": {f"field_{i}": f"value_{i}" for i in range(10)},
            "user_facts": {"butce": "25000$"},
        }
        audit = generate_readiness_audit(full_profile)
        self.assertGreaterEqual(audit["score"], 85)
        self.assertIn("Şampiyonlar Ligi", audit["badge"])

    def test_visa_routes_guide(self):
        prof = {
            "user_facts": {
                "meslek": "Yazılım Mühendisi",
                "egitim": "Yüksek Lisans",
            }
        }
        guide = get_visa_routes_guide(prof)
        self.assertIn("EB-2 NIW", guide)
        self.assertIn("O-1", guide)
        self.assertIn("H-1B", guide)
        self.assertIn("STEM OPT", guide)
        self.assertIn("Sana Özel Stratejik Tavsiye", guide)

    def test_glossary_lookup(self):
        self.assertIn("Consular Electronic Application Center", lookup_glossary("CEAC"))
        self.assertIn("Second Notification Letter", lookup_glossary("2nl"))
        self.assertIn("Public Charge", lookup_glossary("public charge"))
        # Empty query lists all
        all_terms = lookup_glossary("")
        self.assertIn("CEAC", all_terms)
        self.assertIn("2NL", all_terms)


    def test_court_and_timeline_analysis(self):
        from strategy_advisor import analyze_court_and_timeline
        res = analyze_court_and_timeline({"meslek": "Yazılımcı", "hedef_lokasyon": "Austin"})
        self.assertIn("Red Eagle Law", res)
        self.assertIn("Ninth Circuit", res)
        self.assertIn("Senaryo A", res)
        self.assertIn("Senaryo B", res)
        self.assertIn("Senaryo C", res)
        self.assertIn("Yazılımcı", res)

    def test_full_lifecycle_guide(self):
        from strategy_advisor import get_full_lifecycle_guide
        guide = get_full_lifecycle_guide()
        self.assertIn("360° Green Card Sürecinin Eksiksiz Yol Haritası", guide)
        self.assertIn("DS-5501", guide)
        self.assertIn("Unganlar", guide)
        self.assertIn("Credit Score", guide)
        
        single = get_full_lifecycle_guide(7)
        self.assertIn("Faz 7", single)
        self.assertIn("Unganlar", single)


if __name__ == "__main__":
    unittest.main()
