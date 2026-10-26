"""Live public web research with first-class lawyer and community perspectives.

A query about what people/attorneys think NEVER requires .gov verification
as a precondition to displaying their attributable comments. Search snippets
are labelled by provenance, not asserted as established facts.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urlsplit, urlencode
import logging
import os
import re
import threading
import time
import xml.etree.ElementTree as ET

import requests

log = logging.getLogger("GreenCardCloudCoach")
USER_AGENT = "GreenCard27-Research/2.0"
CACHE_SECONDS = 600
_CACHE = {}
_LOCK = threading.Lock()

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
LONG_NUMBER_PATTERN = re.compile(r"\b\d{9,}\b")
PRIVATE_PATTERN = re.compile(
    r"(?:confirmation\s*number|pasaport\s*numaram|passport\s*number|"
    r"tc\s*kimlik|adresim\s*şu|iban|doğum\s*tarihim)", re.IGNORECASE,
)
PERSPECTIVE_WORDS = (
    "reddit", "forum", "yorum", "ne diyor", "ne söyl", "ne düşün",
    "hukukçu", "avukat", "lawyer", "attorney", "community",
    "kullanıcılar", "insanlar", "topluluk", "deneyim", "perspektif",
    "gov harici", ".gov harici", "gayriresm", "sosyal medya",
    "hukuk firm", "tepkiler", "görüş",
)
TOPICS = (
    (("mahkeme", "dava", "temyiz", "injunction", "ruling"),
     "DV 2027 Red Eagle Law Rubio court order appeal status October 2026"),
    (("sonuç", "çekiliş", "kazandım", "selected", "selection"),
     "DV-2027 selection results date Department of State"),
    (("başvuru", "kayıt", "registration", "entry", "son tarih"),
     "DV-2027 registration entry period opening State Department"),
    (("ds-260", "ds260", "ceac"),
     "Diversity Visa selectees DS-260 official instructions"),
    (("fotoğraf", "photo", "biyometrik"),
     "Diversity Visa lottery photo requirements"),
    (("pasaport", "passport"),
     "Diversity Visa passport rule 2027"),
    (("mülakat", "interview", "konsolosluk"),
     "Diversity Visa interview scheduling 2027 embassy"),
    (("vize bülteni", "visa bulletin", "case number"),
     "Visa Bulletin diversity immigrant DV-2027"),
    (("ücret", "fee", "payment"),
     "Diversity Visa DV entry fee State Department 2026"),
    (("sağlık", "aşı", "medical"),
     "Diversity Visa medical examination vaccinations"),
)
DEFAULT_QUERY = "DV-2027 diversity visa latest news Department of State October 2026"


class SearchPrivacyError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    snippet: str
    official: bool
    kind: str = "web"


@dataclass(frozen=True)
class Research:
    query: str
    sources: tuple
    checked_at: str
    status: str
    intent: str = "general"


def is_perspective_question(question: str) -> bool:
    q = (question or "").casefold()
    return any(word in q for word in PERSPECTIVE_WORDS)


def is_official_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        return parts.scheme == "https" and (host.endswith(".gov") or host.endswith(".uscourts.gov"))
    except ValueError:
        return False


def safe_source(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return (
            parts.scheme == "https" and bool(parts.hostname)
            and parts.username is None and parts.password is None
            and len(url) <= 400 and not parts.fragment
        )
    except ValueError:
        return False


def category_for_url(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    if is_official_url(url):
        return "official"
    if host == "reddit.com" or host.endswith(".reddit.com") or host.endswith(".visajourney.com") or host.endswith(".immihelp.com"):
        return "community"
    legal_sites = ("fragomen.com", "aila.org", "redeaglelaw.com", "blasingamelaw.com", "clinchlaw.com", "immigration-analytics.com")
    if any(host == site or host.endswith("." + site) for site in legal_sites):
        return "legal"
    if "news.google.com" in host:
        return "news"
    return "web"


def build_query(question: str, explicit: bool) -> str:
    question = " ".join((question or "").strip().split())
    if explicit:
        if not question:
            return ""
        if EMAIL_PATTERN.search(question) or LONG_NUMBER_PATTERN.search(question) or PRIVATE_PATTERN.search(question):
            raise SearchPrivacyError("Search query contains personal identifiers")
        return question[:160]
    if is_perspective_question(question):
        return "DV-2027 Red Eagle Law v Rubio lawyer analysis Reddit forum discussion October 2026"
    lower = question.casefold()
    for needles, query in TOPICS:
        if any(word in lower for word in needles):
            return query
    return DEFAULT_QUERY


def search_queries(question: str, explicit: bool = False) -> tuple:
    """Multi-source discovery only when the user wants opinions or experiences."""
    root = build_query(question, explicit)
    if not root:
        return ()
    if not is_perspective_question(question):
        return (root,)
    text = question.casefold()
    if "dv-2028" in text:
        anchor = "DV-2028 diversity visa"
    elif "dv-2027" in text or "bu durum" in text or "mahkeme" in text or "dava" in text:
        anchor = "DV-2027 Red Eagle Law Rubio"
    else:
        # Explicit, non-sensitive user question can be searched as written.
        anchor = root[:90] if explicit else "DV-2027 diversity visa"
    return (
        f"{anchor} immigration attorney law firm analysis appeal October 2026",
        f"site:reddit.com {anchor} users discussion comments October 2026",
        f"site:visajourney.com OR site:immigration-analytics.com {anchor} reaction",
    )


def _normalize(raw: dict, kind: str = "web") -> Source | None:
    title = unescape(re.sub(r"<[^>]+>", " ", str(raw.get("title", "")))).strip()[:155]
    url = str(raw.get("href") or raw.get("url") or "").strip()
    snippet = unescape(re.sub(r"<[^>]+>", " ", str(raw.get("body") or raw.get("snippet") or ""))).strip()[:460]
    if not title or not safe_source(url):
        return None
    identified = category_for_url(url)
    return Source(title, url, snippet, is_official_url(url), identified if identified != "web" else kind)


def _news_fallback(query: str):
    url = "https://news.google.com/rss/search?" + urlencode({
        "q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"
    })
    response = requests.get(url, timeout=7, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    if len(response.content) > 700_000:
        raise ValueError("RSS size limit")
    root = ET.fromstring(response.content)
    entries = []
    for item in root.findall(".//item")[:6]:
        src = _normalize({
            "title": item.findtext("title", ""),
            "href": item.findtext("link", ""),
            "body": "Google News tarafından listelenen haber başlığı",
        }, "news")
        if src:
            entries.append(src)
    return entries


def _reddit_fallback(query: str):
    """Public Reddit Atom feed (may be blocked by Reddit on some hosts)."""
    url = "https://www.reddit.com/r/immigration/search.rss?" + urlencode({
        "q": query, "restrict_sr": "on", "sort": "new", "t": "month"
    })
    response = requests.get(url, timeout=6, headers={
        "User-Agent": USER_AGENT + " (public community results)"
    })
    response.raise_for_status()
    if len(response.content) > 600_000:
        raise ValueError("RSS size limit")
    root = ET.fromstring(response.content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entries = []
    for entry in root.findall("a:entry", ns)[:4]:
        title = entry.findtext("a:title", "", ns)
        permalink = ""
        for link in entry.findall("a:link", ns):
            if link.attrib.get("rel") in ("alternate", None):
                permalink = link.attrib.get("href", "")
                break
        snippet = entry.findtext("a:content", "", ns) or entry.findtext("a:summary", "", ns)
        src = _normalize({"title": title, "href": permalink, "body": snippet}, "community")
        if src:
            entries.append(src)
    return entries


def _curated_sources(sources: list, perspective: bool) -> list:
    seen = set()
    unique = []
    for src in sources:
        key = src.url.split("?", 1)[0].rstrip("/")
        if key not in seen:
            seen.add(key)
            if perspective and src.official:
                continue  # The user explicitly requested non-government views.
            unique.append(src)
    if not perspective:
        return sorted(unique, key=lambda x: (not x.official, x.kind == "news"))[:5]
    selected = []
    for kind, count in (("legal", 2), ("community", 2), ("web", 1), ("news", 1)):
        for src in unique:
            if src.kind == kind and src not in selected and len([s for s in selected if s.kind == kind]) < count:
                selected.append(src)
    for src in unique:
        if src not in selected and len(selected) < 6:
            selected.append(src)
    return selected[:6]


def research_web(question: str, explicit: bool = False) -> Research:
    queries = search_queries(question, explicit)
    perspective = is_perspective_question(question)
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    root = queries[0] if queries else ""
    if os.getenv("WEB_RESEARCH_ENABLED", "true").strip().lower() in ("false", "0", "off"):
        return Research(root, (), checked_at, "disabled", "perspective" if perspective else "general")
    if not queries:
        return Research(root, (), checked_at, "no_query", "perspective" if perspective else "general")
    key = (queries, perspective)
    with _LOCK:
        entry = _CACHE.get(key)
        if entry and entry[0] > time.monotonic():
            return entry[1]
    items = []
    try:
        from ddgs import DDGS
        search = DDGS(timeout=7)
        for query in queries:
            try:
                found = search.text(query, max_results=6, backend="auto", region="us-en")
                items.extend(s for row in found if (s := _normalize(row)))
            except Exception as exc:
                log.warning("Arama motoru hata=%s", type(exc).__name__)
    except Exception as exc:
        log.warning("DDGS başlatılamadı: hata=%s", type(exc).__name__)

    has_legal = any(s.kind == "legal" for s in items)
    has_community = any(s.kind == "community" for s in items)
    if not items or (perspective and not has_legal):
        try:
            items.extend(_news_fallback(queries[0]))
        except Exception as exc:
            log.warning("Google News RSS hata=%s", type(exc).__name__)
    if perspective and not has_community:
        try:
            items.extend(_reddit_fallback("DV-2027"))
        except Exception as exc:
            log.info("Reddit RSS erişilemedi: %s", type(exc).__name__)
    ranked = _curated_sources(items, perspective)
    result = Research(root, tuple(ranked), checked_at, "ok" if ranked else "unavailable",
                      "perspective" if perspective else "general")
    with _LOCK:
        _CACHE[key] = (time.monotonic() + CACHE_SECONDS, result)
        if len(_CACHE) > 80:
            _CACHE.pop(next(iter(_CACHE)))
    log.info("Web arama: niyet=%s durum=%s kaynak=%s",
             result.intent, result.status, len(result.sources))
    return result


def web_context(result: Research) -> str:
    if not result.sources:
        return "Bu sorgu için arama servisleri kaynak döndürmedi."
    lines = [f"Web arama zamanı UTC: {result.checked_at}",
             "Aşağıdakiler arama sonucu özeti; tam makalenin veya yorumların tamamı okunmuş sayılmaz."]
    for i, src in enumerate(result.sources, 1):
        label = {"official":"Kamu kurumu","legal":"Hukuk firması/yayın",
                 "community":"Forum/kullanıcı", "news":"Haber", "web":"Diğer site"}.get(src.kind, "Web")
        lines.append(f"[{i}] {label}: {src.title}\nBağlantı: {src.url}\nBulunan metin: {src.snippet}")
    return "\n\n".join(lines)[:4900]


def source_links(result: Research, max_sources: int = 4) -> str:
    if not result.sources:
        return ""
    lines = ["\n\nKaynak bağlantıları:"]
    for i, src in enumerate(result.sources[:max_sources], 1):
        label = {"legal":"Hukuk","community":"Forum","news":"Haber","official":"Resmî",
                 "web":"Web"}.get(src.kind, "Web")
        lines.append(f"{i}. {label}: {src.url}")
    return "\n".join(lines)[:1250]


def perspective_digest(result: Research) -> str:
    """Useful sourced answer even if Gemini is offline; no unrelated checklist."""
    if not result.sources:
        return (
            "Hukukçu veya forum görüşleri için arama denendi, ancak erişilebilir sonuç gelmedi. "
            "Bu, internette görüş olmadığı anlamına gelmiyor. "
            "Arama servisi geçici olarak engellenmiş olabilir. "
            "Alternatif olarak '/ara DV-2027 Red Eagle Law yorumlar' komutunu kullan."
        )
    groups = (("legal", "Hukukçuların / hukuk yayınlarının paylaştıkları"),
              ("community", "Forum ve kullanıcıların yazdıkları"),
              ("web", "Diğer kaynaklar"), ("news", "Basında aktarılanlar"))
    lines = ["DV-2027 hakkında internette bulduğum görüş ve tartışmalar:"]
    for kind, title in groups:
        entries = [x for x in result.sources if x.kind == kind]
        if not entries:
            continue
        lines.append("\n" + title + ":")
        for source in entries[:2]:
            text = source.snippet or "Arama sonucu özet metni gelmedi; bağlantıda ayrıntı olabilir."
            lines.append(f"• {source.title}: {text[:250]}\n{source.url}")
    lines.append("\nBu özet kaynaklarda görünen yazılardan çıkarıldı; doğrulanmış mahkeme kararı ile yorumları ayrı değerlendirmek gerekir.")
    return "\n".join(lines)[:3850]
