import unittest
from unittest.mock import patch
import gemini_runtime as gm


class FakeModel:
    def __init__(self, name, actions=("generateContent",)):
        self.name = "models/" + name
        self.supported_actions = actions


class FakeError(Exception):
    def __init__(self, code):
        super().__init__("simulated")
        self.code = code


class FakeModels:
    def __init__(self, names, failures=None):
        self.names = names
        self.failures = failures or {}
        self.calls = []

    def list(self):
        return [FakeModel(name) for name in self.names]

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        if model in self.failures:
            raise FakeError(self.failures[model])
        return type("Response", (), {"text": "OK"})()


class FakeClient:
    def __init__(self, models):
        self.models = models


class ModelRoutingTests(unittest.TestCase):
    def setUp(self):
        with gm._cache_lock:
            gm._cached_available = None
            gm._cache_until = 0
            gm._last_good = None

    def test_2_5_legacy_is_not_primary(self):
        names = gm.candidates("gemini-2.5-flash")
        self.assertEqual(names[0], "gemini-3.5-flash-lite")
        self.assertEqual(names[-1], "gemini-2.5-flash")

    def test_list_models_filters_unavailable_or_unsupported(self):
        models = FakeModels(["gemini-3.8-flash", "gemini-2.5-flash"])
        available = gm.discover_available(FakeClient(models))
        self.assertEqual(available, {"gemini-3.8-flash", "gemini-2.5-flash"})

    def test_select_listed_3_8_when_3_5_is_missing(self):
        models = FakeModels(["gemini-3.8-flash"])
        response, selected = gm.generate_with_fallback(FakeClient(models), "gemini-2.5-flash", "hi", None)
        self.assertEqual(selected, "gemini-3.8-flash")
        self.assertEqual(response.text, "OK")

    def test_404_falls_back_to_another_free_model(self):
        models = FakeModels(list(gm.FREE_TEXT_MODELS), {"gemini-3.5-flash-lite": 404})
        response, selected = gm.generate_with_fallback(FakeClient(models), None, "hi", None)
        self.assertEqual(selected, "gemini-3.8-flash")
        self.assertEqual(models.calls, ["gemini-3.5-flash-lite", "gemini-3.8-flash"])

    def test_429_does_not_retry_other_models(self):
        models = FakeModels(list(gm.FREE_TEXT_MODELS), {"gemini-3.5-flash-lite": 429})
        with self.assertRaises(FakeError):
            gm.generate_with_fallback(FakeClient(models), None, "hi", None)
        self.assertEqual(models.calls, ["gemini-3.5-flash-lite"])

    def test_no_allowed_models_fails_without_generate(self):
        models = FakeModels(["gemini-4-argon"])
        with self.assertRaises(gm.ModelAccessError):
            gm.generate_with_fallback(FakeClient(models), None, "hi", None)
        self.assertEqual(models.calls, [])

    def test_unknown_override_not_used(self):
        self.assertNotIn("gemini-4-argon", gm.candidates("gemini-4-argon"))

    def test_non_404_error_propagates(self):
        models = FakeModels(list(gm.FREE_TEXT_MODELS), {"gemini-3.5-flash-lite": 403})
        with self.assertRaises(FakeError):
            gm.generate_with_fallback(FakeClient(models), None, "hi", None)
        self.assertEqual(len(models.calls), 1)


if __name__ == "__main__":
    unittest.main()
