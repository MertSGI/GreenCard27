"""Google Gemini free-tier text-model selector for GreenCard27.

No paid fallback and no Google Search grounding. Only a short, curated
free-tier text-model allowlist is used. Model availability is verified against
the API key's models.list() when available; 404 leads to the next model.
403/429 and other errors do not trigger retry storms.
"""
import logging
import threading
import time

log = logging.getLogger("GreenCardCloudCoach")

FREE_TEXT_MODELS = (
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
)
LEGACY_FREE_TEXT_MODELS = ("gemini-2.5-flash",)
ALLOWLIST = FREE_TEXT_MODELS + LEGACY_FREE_TEXT_MODELS

_cache_lock = threading.Lock()
_cached_available = None
_cache_until = 0.0
_last_good = None


def error_code(exc):
    try:
        return int(getattr(exc, "code", None))
    except (TypeError, ValueError):
        return None


def active_model():
    with _cache_lock:
        return _last_good


def candidates(preferred=None, available=None):
    """Prefer currently supported free-tier models, then an explicitly selected legacy one."""
    preferred = (preferred or "").strip().replace("models/", "")
    if preferred and preferred not in ALLOWLIST:
        log.warning("GEMINI_MODEL ücretsiz metin-modeli allowlist dışında; göz ardı ediliyor: %s", preferred)
    # Legacy model erişimi kısıtlandığından yeni Flash modelleri önce gelir.
    order = list(FREE_TEXT_MODELS)
    if preferred in FREE_TEXT_MODELS:
        order.remove(preferred)
        order.insert(0, preferred)
    if preferred in LEGACY_FREE_TEXT_MODELS:
        order.append(preferred)
    with _cache_lock:
        last = _last_good
    if last in order:
        order.remove(last)
        order.insert(0, last)
    if available is not None:
        allowed = set(available)
        order = [m for m in order if m in allowed]
    return order


def discover_available(client):
    """Read only models supporting generateContent; cache results for 15 minutes."""
    global _cached_available, _cache_until
    now = time.monotonic()
    with _cache_lock:
        if _cache_until > now and _cached_available is not None:
            return set(_cached_available)
    try:
        found = set()
        for m in client.models.list():
            name = str(getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None)
            if name in ALLOWLIST and (actions is None or "generateContent" in actions):
                found.add(name)
        with _cache_lock:
            _cached_available = frozenset(found)
            _cache_until = time.monotonic() + 900
        log.info("Google models.list tamamlandı: izinli_modeller=%s", sorted(found))
        return found
    except Exception as exc:
        log.warning("Google models.list okunamadı: hata=%s kod=%s", type(exc).__name__, error_code(exc))
        # When the model-list endpoint is unavailable, model calls can still be tried.
        return None


class ModelAccessError(Exception):
    code = 404

    def __init__(self, message="API anahtarı için izin verilen ücretsiz Flash modeli bulunamadı."):
        super().__init__(message)


def generate_with_fallback(client, preferred, contents, config):
    """Return (response, selected_model). Only retry a model-specific 404."""
    global _last_good
    accessible = discover_available(client)
    names = candidates(preferred, accessible)
    if not names:
        raise ModelAccessError("Google models.list ücretsiz metin modeli göstermiyor.")
    last_not_found = None
    for name in names:
        try:
            response = client.models.generate_content(
                model=name, contents=contents, config=config,
            )
            with _cache_lock:
                _last_good = name
            return response, name
        except Exception as exc:
            code = error_code(exc)
            log.warning("Gemini model çağrısı başarısız: model=%s hata=%s kod=%s", name, type(exc).__name__, code)
            if code != 404:
                # 429 quota / 403 auth / 500 network should never fan out across models.
                raise
            last_not_found = exc
    raise ModelAccessError(
        "Denediğimiz ücretsiz modeller 404 döndürdü; anahtarın kullanılabilir modellerini kontrol edin."
    ) from last_not_found
