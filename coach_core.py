"""Practical personal daily planning, actionable next steps, and 2-news strategic scenario analysis."""
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable


def due(profile: Dict[str, Any], date: str, hour: int) -> bool:
    """Return True if daily coaching digest is due between 09:00 and 23:00 and not sent today."""
    return 9 <= hour < 23 and profile.get("last_daily_digest") != date


def format_news_item(item: Dict[str, str]) -> str:
    """Format a single news item with working direct link, source, summary, and process impact."""
    title = item.get("title", "Green Card Süreç Haberi").strip()
    link = item.get("link", "").strip()
    source = item.get("source", "Haber Kaynağı").strip()
    summary = item.get("summary", "").strip() or item.get("body", "").strip()
    impact = item.get("impact", "").strip()

    lines = [f"📰 *{title}*"]
    if source:
        lines.append(f"🏛️ *Kaynak:* {source}")
    if link:
        lines.append(f"🔗 {link}")
    if summary:
        lines.append(f"📝 *Özet:* _{summary[:280]}_")
    if impact:
        lines.append(f"⚖️ *Sürece Etkisi:* {impact[:250]}")
    return "\n".join(lines)


def _derive_rule_based_scenarios(top_two: List[Dict[str, str]], profile: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Build deterministic 'what could happen' and 'how we must prepare' insights from 2 news items."""
    facts = profile.get("user_facts", {}) if profile else {}
    job = facts.get("meslek", "").strip()
    target = facts.get("hedef_lokasyon", "").strip()
    case_no = facts.get("case_number", "").strip()

    combined = " ".join(
        f"{h.get('title', '')} {h.get('summary', '')} {h.get('impact', '')} {h.get('body', '')}"
        for h in top_two
    ).lower()

    scenarios: List[str] = []
    preparations: List[str] = []

    if any(k in combined for k in ("stay", "appeal", "ninth circuit", "court", "lawsuit", "red eagle", "judge")):
        scenarios.append(
            "• *Hukuki / Takvim Olasılığı:* Temyiz süreci sonuçlandığında veya yeni bir davada tedbir kararı çıkarsa, "
            "başvuru portalı beklenmedik bir tarihte ve *daraltılmış (30 gün veya daha kısa)* bir pencereyle aniden açılabilir; "
            "alternatif olarak gecikme DV-2028 dönemine sarkabilir."
        )
        preparations.append(
            "• *Teknik Hazırlık Kalkanı:* Başvuru açıldığı gün sistem kilitlenmeden işlem yapabilmek için 600x600 px biyometrik fotoğrafınızı "
            "(`/fotograf`) ve 1$ ödemeye açık kartınızı şimdiden hazır tutun."
        )

    if any(k in combined for k in ("transfer", "kcc", "embassy", "consulate", "interview", "visa bulletin", "ankara", "taşıma", "backlog")):
        scenarios.append(
            "• *Konsolosluk / Dosya Taşıma Olasılığı:* Ankara ve yoğun konsolosluklarda mülakat beklemeleri uzayabilir; "
            "ancak yeni 2025–2026 kuralları gereği oturum/çalışma izni olmayan üçüncü ülkelere dosya taşıma talepleri reddedilebilir."
        )
        preparations.append(
            "• *Transfer ve Evrak Önlemi:* Farklı bir ülkede oturum hakkınız varsa DS-260 kilidi açtırma ve KCC transfer belgelerinizi "
            "`/dosya_tasima` üzerinden hazır edin; yoksa DS-260 ve e-Devlet evraklarınızı ilk haftadan kusursuz sunun."
        )

    if any(k in combined for k in ("fee", "1$", "dollar", "electronic", "rule")):
        scenarios.append(
            "• *Ödeme ve Sistem Değişikliği Olasılığı:* 1$ kayıt harcı ve ek güvenlik doğrulamaları ilk günlerde ödeme/oturum hatalarına yol açabilir."
        )
        preparations.append(
            "• *Ödeme Tedbiri:* 3D Secure / yurtdışı internet alışverişine açık en az iki farklı banka/kredi kartını hazırda bekletin."
        )

    if not scenarios:
        scenarios.append(
            "• *Süreç Projeksiyonu:* Güncel gelişmeler, idari kuralların ve mahkeme kararlarının başvuru ile mülakat pencerelerini "
            "kısa sürede değiştirebileceğine işaret ediyor; bekle-gör yaklaşımı hak kaybı yaratabilir."
        )
        preparations.append(
            "• *Çok Yönlü Hazırlık:* Çekiliş ve vize süreçlerini tek kanala bağlamayın; e-Devlet adres/SGK dökümlerinizi `/ds260`'a kaydedip "
            "alternatif B planı vize rotalarınızı (`/vize_rotalari` veya `/vize_analiz`) değerlendirin."
        )

    # Kullanıcı profiline özel ek hazırlık satırı
    if job or target or case_no:
        who = ", ".join(x for x in (job, target, case_no) if x)
        preparations.append(
            f"• *Sana Özel Not ({who}):* Gelişmeler sürerken kendi dosyan ve kariyer planın için "
            "B planını (`/vize_analiz`) ve bütçe/runway dengeni (`/hesapla`) güncel tutmalıyız."
        )

    return scenarios, preparations


def analyze_daily_news_scenarios(
    headlines: List[Dict[str, str]],
    profile: Dict[str, Any],
    ai_callable: Optional[Callable[[str], str]] = None,
) -> str:
    """Analyze the top 2 daily news items with strategic 'what could happen / how to prepare' reasoning."""
    top_two = (headlines or [])[:2]
    if not top_two:
        return (
            "📰 *Günün 2 Haberi & Stratejik Senaryo Analizi*\n"
            "Şu an canlı haber akışına ulaşılamadı; ancak Red Eagle Law temyiz süreci ve konsolosluk "
            "yoğunlukları ışığında pasaport, fotoğraf (`/fotograf`), DS-260 (`/ds260`) ve B planı (`/vize_analiz`) "
            "hazırlıklarımızı eksiksiz tutmaya devam etmeliyiz."
        )

    lines = ["📰 *GÜNÜN 2 KRİTİK HABERİ & STRATEJİK SENARYO YORUMU*", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for idx, item in enumerate(top_two, 1):
        lines.append(f"*{idx}) {item.get('title', 'Haber').strip()}*")
        src = item.get("source", "").strip()
        lnk = item.get("link", "").strip()
        if src:
            lines.append(f"🏛️ Kaynak: {src}")
        if lnk:
            lines.append(f"🔗 {lnk}")
        lines.append("")

    facts = profile.get("user_facts", {}) if profile else {}
    profile_summary = ", ".join(f"{k}={v}" for k, v in facts.items() if v) or "Genel ABD vize/Green Card adayı"

    ai_text = ""
    if ai_callable is not None:
        news_dump = "\n\n".join(
            f"Haber {i}: {h.get('title', '')}\nKaynak: {h.get('source', '')}\nÖzet: {h.get('summary') or h.get('body', '')}\nEtki: {h.get('impact', '')}"
            for i, h in enumerate(top_two, 1)
        )
        prompt = (
            "Sen kullanıcının kıdemli ABD göçmenlik danışmanı ve stratejik koçusun. "
            "Aşağıdaki GÜNÜN 2 GÜNCEL HABERİ üzerine derinlemesine düşün.\n\n"
            f"Kullanıcı Profili: {profile_summary}\n\n"
            f"{news_dump}\n\n"
            "Yanıtını TAM OLARAK şu iki başlık altında Türkçe, somut ve net yaz:\n"
            "🔮 *Bu Şekilde Olabilir (Olası Senaryolar):*\n"
            "(Bu 2 haberin mahkeme, dosya taşıma, konsolosluk yoğunluğu veya vize kuralları açısından nelere yol açabileceğini 2-3 maddede yorumla)\n\n"
            "🛡️ *Böyle Hazır Olmalıyız (Somut Aksiyon Planı):*\n"
            "(Bu olasılıklara karşı kullanıcının bugün hangi somut adımları atarak gardını alması gerektiğini 2-3 maddede söyle)"
        )
        try:
            ai_text = (ai_callable(prompt) or "").strip()
        except Exception:
            ai_text = ""

    if ai_text:
        lines.append(ai_text[:2200])
    else:
        scenarios, preparations = _derive_rule_based_scenarios(top_two, profile)
        lines.append("🔮 *Bu Şekilde Olabilir (Olası Senaryolar):*")
        lines.extend(scenarios)
        lines.append("")
        lines.append("🛡️ *Böyle Hazır Olmalıyız (Somut Hazırlık Planı):*")
        lines.extend(preparations)

    return "\n".join(lines).strip()


def digest(
    profile: Dict[str, Any],
    checklist: list,
    when: datetime,
    headlines: Optional[List[Dict[str, str]]] = None,
    ai_callable: Optional[Callable[[str], str]] = None,
) -> str:
    """Generate high-yield, personalized daily coaching brief with 2-news strategic scenario commentary."""
    checks = profile.get("checklist", {})
    done = sum(bool(checks.get(k)) for k, _ in checklist)
    upcoming = [label for k, label in checklist if not checks.get(k)]
    facts = profile.get("user_facts", {})
    job = facts.get("meslek")
    target_loc = facts.get("hedef_lokasyon")
    budget = facts.get("butce")
    case_no = facts.get("case_number")

    lines = [
        f"☀️ *GREEN CARD & ABD VİZE KOÇUNUZ* • {when:%d.%m.%Y}",
        f"📊 *Genel Hazırlık İlerlemesi:* {done}/{len(checklist)} Adım Tamamlandı",
    ]

    profile_parts = []
    if job:
        profile_parts.append(f"💼 {job}")
    if target_loc:
        profile_parts.append(f"📍 {target_loc}")
    if budget:
        profile_parts.append(f"💵 {budget}")
    if case_no:
        profile_parts.append(f"🔢 {case_no}")
    if profile_parts:
        lines.append(f"👤 *Danışan Durumu:* {' | '.join(profile_parts)}")

    lines.extend([
        "",
        "🎯 *BUGÜNKÜ SOMUT ADIMLAR:*",
    ])

    if upcoming:
        for i, task in enumerate(upcoming[:2], 1):
            lines.append(f"{i}. {task}")
    else:
        lines.append("🎉 Tebrikler! Tüm checklist maddeleriniz tamamlandı. Resmî bültenleri ve dosya güncelliğini takip ediyoruz.")

    lines.extend([
        "",
        "💡 *Koçun Günlük Tavsiyesi:* Süreci sadece beklemeyle geçirmeyin. Pasaport, fotoğraf ve e-Devlet evraklarınızı tamamlayıp dosya taşıma / B planı vize rotalarınızı da paralel hazır tutun.",
        "",
        "⚖️ *Mahkeme ve Süreç Özeti:* 9. Temyiz Mahkemesi (Ninth Circuit) yürütmeyi durdurma kararı sonrasında portal askıda; Dışişleri Bakanlığı'nın duyurusu bekleniyor.",
        "Resmî Duyurular: https://travel.state.gov/en/newsroom/visas/2025/changes-to-2027-dv-program-entry-period.html",
        "Vize Düzenleme: https://travel.state.gov/en/newsroom/visas/2025/diversity-visa-issuance-updated-guidance.html",
    ])

    if headlines:
        lines.append("")
        lines.append(analyze_daily_news_scenarios(headlines, profile, ai_callable=ai_callable))

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚡ *Hızlı Komutlar:* /bugun /haber_analiz /dosya_tasima /vize_analiz /karne /checklist /ara",
    ])
    return "\n".join(lines)[:3900]


def new_headlines(current: List[Dict[str, str]], seen: List[str]) -> List[Dict[str, str]]:
    """Filter newly discovered news that haven't been broadcasted yet."""
    if not seen:
        return []
    prior = set(seen)
    return [i for i in current if i.get("id") not in prior][:3]
