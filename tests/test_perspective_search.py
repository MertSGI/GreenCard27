import unittest
from unittest.mock import patch
import web_research as wr
import greencard_telegram_bot as bot


class PerspectivesTests(unittest.TestCase):
    def setUp(self):
        wr._CACHE.clear()

    def test_opinion_request_detected_in_turkish(self):
        q = ".gov harici internette kullanıcılar hukukçular bu durum ile ilgili ne söylüyorlar"
        self.assertTrue(wr.is_perspective_question(q))
        searches = wr.search_queries(q)
        self.assertEqual(len(searches), 3)
        self.assertTrue(any("reddit.com" in x for x in searches))
        self.assertTrue(any("immigration attorney" in x for x in searches))
        self.assertFalse(all(".gov" in x for x in searches))

    def test_diversify_actual_lawyer_and_user_sources(self):
        a = wr._normalize({"title":"Firm perspective",
                           "href":"https://www.fragomen.com/insights/dv-2027.html",
                           "body":"A possible appeal may affect the registration timeline."})
        b = wr._normalize({"title":"Reddit discussion",
                           "href":"https://www.reddit.com/r/immigration/comments/example",
                           "body":"Some entrants are hopeful but worried."})
        c = wr._normalize({"title":"Government advisory",
                           "href":"https://travel.state.gov/info",
                           "body":"Official statement."})
        selected = wr._curated_sources([c,b,a], perspective=True)
        self.assertEqual({x.kind for x in selected}, {"legal","community"})
        self.assertTrue(all(not x.official for x in selected))
        result = wr.Research("DV-2027",tuple(selected),"2026-10-26T10:00:00+00:00","ok","perspective")
        answer = wr.perspective_digest(result)
        self.assertIn("Firm perspective",answer)
        self.assertIn("Reddit discussion",answer)
        self.assertNotIn("checklist",answer.casefold())
        self.assertIn("https://www.reddit.com",answer)

    def test_no_fake_offline_opinions(self):
        result=wr.Research("DV-2027",(),"2026-10-26T10:00:00+00:00","unavailable","perspective")
        msg=wr.perspective_digest(result)
        self.assertIn("sonuç gelmedi",msg)
        self.assertNotIn("yalnızca resmî",msg)

    def test_bot_keeps_user_focus_when_gemini_down(self):
        src=wr.Source("Forum","https://reddit.com/r/immigration/comments/a",
                      "Applicants disagree on the timing.",False,"community")
        found=wr.Research("DV-2027",(src,),"2026-10-26T10:00:00+00:00","ok","perspective")
        with patch.object(bot,"research_web",return_value=found), \
             patch.object(bot,"HAS_GENAI",False):
            reply=bot.answer_user_question(
                "Hukukçular ve forumlarda ne diyorlar?",{"checklist":{}},False)
        self.assertIn("Applicants disagree",reply)
        self.assertNotIn("pasaportun hazır",reply.casefold())

    def test_non_perspective_still_searches_official(self):
        query=wr.build_query("Başvuru tarihleri nedir?",False)
        self.assertIn("registration",query)


if __name__=="__main__":
    unittest.main()
