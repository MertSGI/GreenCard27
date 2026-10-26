import unittest
from unittest.mock import patch
import web_research as web


class WebResearchTests(unittest.TestCase):
    def setUp(self):
        web._CACHE.clear()

    def test_generic_chat_query_never_leaks_passport_or_email(self):
        query = web.build_query(
            "Benim pasaport numaram 123456789 ve adım Yilmaz. Ne yapacağım?", False)
        self.assertIn("passport", query)
        self.assertNotIn("123456789", query)
        self.assertNotIn("Yilmaz", query)

    def test_explicit_personal_identifiers_rejected(self):
        for value in ("mailim foo@example.com", "pasaport numaram A12344567", "id 123456789"):
            with self.assertRaises(web.SearchPrivacyError):
                web.build_query(value, True)

    def test_user_requested_topic_sent_unmodified_within_limit(self):
        self.assertEqual(web.build_query("DV-2027 dava durumu", True), "DV-2027 dava durumu")

    def test_only_real_https_gov_is_official(self):
        self.assertTrue(web.is_official_url("https://travel.state.gov/path"))
        self.assertFalse(web.is_official_url("https://state.gov.bad.example/path"))
        self.assertFalse(web.is_official_url("http://travel.state.gov/path"))

    def test_source_rejects_non_https_links(self):
        self.assertIsNone(web._normalize({"title": "Example", "href": "http://example.com", "body": "text"}))
        self.assertIsNone(web._normalize({"title": "Example", "href": "file:///etc/passwd", "body": "text"}))

    def test_fallback_and_no_hallucinated_evidence(self):
        with patch("web_research._news_fallback", return_value=[]):
            import sys, types
            module = types.ModuleType("ddgs")
            class BrokenDDGS:
                def __init__(self, **kwargs):
                    pass
                def text(self, *args, **kwargs):
                    raise OSError("simulated")
            module.DDGS = BrokenDDGS
            with patch.dict(sys.modules, {"ddgs": module}):
                result = web.research_web("mahkeme")
        self.assertEqual(result.status, "unavailable")
        self.assertFalse(result.sources)
        self.assertIn("kaynak sağlamadı", web.web_context(result))

    def test_official_source_sorted_first(self):
        with patch("web_research._news_fallback", return_value=[]):
            import sys, types
            module = types.ModuleType("ddgs")
            class FakeDDGS:
                def __init__(self, **kwargs):
                    pass
                def text(self, *args, **kwargs):
                    return [
                        {"title": "News", "href": "https://news.example.com/dv", "body": "News"},
                        {"title": "Official", "href": "https://travel.state.gov/a", "body": "Official"},
                    ]
            module.DDGS = FakeDDGS
            with patch.dict(sys.modules, {"ddgs": module}):
                result = web.research_web("DV 2027", explicit=True)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.sources[0].official, True)
        self.assertIn("travel.state.gov", web.source_links(result))


if __name__ == "__main__":
    unittest.main()
