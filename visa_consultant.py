"""360° US Visa Consultancy, Case Transfer & DS-260 Consistency Audit Engine.

Brings professional US immigration consultancy capabilities into GreenCard27:
1. Case Transfer (Dosya Taşıma) & Consular Strategy + English Official Letter Generator
2. Comprehensive US Visa Eligibility Assessment (DV, EB-2 NIW, O-1, E-2, F-1, B1/B2 214(b), H-1B, L-1)
3. DS-260 "Three-Pair-of-Eyes" Consistency, Turkish-Character & 221(g) Risk Audit
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Callable

from strategy_advisor import parse_numeric_budget, analyze_case_number


TURKISH_CHARS_PATTERN = re.compile(r"[çğıöşüÇĞİÖŞÜ]")


def build_transfer_policy_overview() -> str:
    """Return current 2025-2026 Department of State rules for Case Transfer & TCN appointments."""
    return (
        "✈️ *Dosya Taşıma (Case Transfer) & Konsolosluk Transfer Stratejisi (2025–2026 Güncel Kurallar)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚖️ *1. TEMEL KURAL (Oturum / Vatandaşlık Şartı):*\n"
        "ABD Dışişleri Bakanlığı ve KCC'nin sıkılaştırılmış politikasına göre, mülakatların "
        "*yasal ikamet edilen (oturum izni/çalışma/öğrenci izni bulunan)* veya *vatandaş olunan* "
        "ülkede yapılması esastır. Sırf 'randevu sırası daha hızlı' diye turistik vizeyle başka bir "
        "ülkeye (eski yıllarda yapılan Umman, Hong Kong vb. gibi) dosya taşıma talepleri büyük oranda *reddedilmektedir*.\n\n"
        "📌 *2. AŞAMAYA GÖRE DOĞRU MUHATAP KİMDİR?*\n"
        "• *Mülakat Tarihi (2NL) Henüz Gelmediyse (Dosya KCC'de):*\n"
        "  1) `KCCDV@state.gov` adresine yazarak DS-260 formunuzun kilidini açtırın (*Unlock Request*).\n"
        "  2) Yeni ülkenin adresini/oturumunu formda güncelleyip tekrar onaylayın.\n"
        "  3) İkamet kartı/oturum kanıtınızı ekleyerek KCC'den yeni konsolosluğa (*Post*) yönlendirme isteyin.\n"
        "• *2NL (Mülakat Mektubu) Geldiyse (Dosya Ankara Konsolosluğu'nda):*\n"
        "  Bu aşamada KCC artık dosya taşımaz! Doğrudan *gitmek istediğiniz ülkenin ABD Konsolosluğu* "
        "(Immigrant Visa Navigator) üzerinden kabul talep etmelisiniz. İstisnai aciliyet veya "
        "ilgili ülkede yasal oturum belgeniz olmadan Ankara'dan transfer onayı almak çok zordur.\n\n"
        "⚡ *3. GÖÇMEN OLMAYAN VİZELERDE (B1/B2, F-1) RANDEVU & TCN KURALLARI:*\n"
        "• Güncel `ustraveldocs.com` sisteminde sık aralıklarla bot/otomasyon sorgusu atmak hesabı bloke ettirebilir.\n"
        "• Yalnızca okul başlangıcı (F-1), tıbbi aciliyet veya kanıtlı acil iş toplantısı varsa "
        "resmî portaldan *Acil Randevu (Expedited Appointment)* gerekçesi sunulabilir.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📝 *KİŞİYE ÖZEL İNGİLİZCE DİLEKÇE ÜRETİMİ:*\n"
        "Senaryonuzu komutun devamına yazarak hazır İngilizce e-posta alabilirsiniz:\n"
        "• `/dosya_tasima unlock` _(DS-260 kilidi açtırma dilekçesi)_\n"
        "• `/dosya_tasima Viyana oturum iznim var, dosyamı taşımak istiyorum` _(KCC / Konsolosluk Transfer Dilekçesi)_\n"
        "• `/dosya_tasima B1 B2 acil randevu` _(Expedited Appointment talep taslağı)_"
    )


def _extract_case_and_identity(profile: Dict[str, Any]) -> Dict[str, str]:
    ds260 = profile.get("ds260", {})
    facts = profile.get("user_facts", {})
    full_name = ds260.get("full_name", "").strip() or "[AD SOYAD - PASAPORTTAKİ GİBİ]"
    birth_info = ds260.get("birth_info", "").strip() or "[DOĞUM TARİHİ: YYYY-MM-DD]"
    case_no = facts.get("case_number", "").strip() or "[CASE NUMBER: ÖRN 2027EU000XXXXX]"
    return {
        "full_name": full_name,
        "birth_info": birth_info,
        "case_no": case_no,
    }


def _detect_transfer_intent(scenario: str) -> str:
    s = (scenario or "").casefold()
    if any(k in s for k in ("unlock", "kilit", "açtır", "düzelt", "güncelle")):
        return "unlock"
    if any(k in s for k in ("acil randevu", "expedit", "erken randevu")) or (
        any(k in s for k in ("b1", "b2", "f1", "f-1")) and "taşı" not in s and "transfer" not in s
    ):
        return "expedited"
    return "transfer"


def _build_template_letter(intent: str, scenario: str, identity: Dict[str, str]) -> str:
    if intent == "unlock":
        return (
            "📧 *KCC DS-260 Kilit Açma (Unlock) Resmi E-Posta Taslağı*\n"
            "• *Alıcı:* `KCCDV@state.gov`\n"
            f"• *Subject:* `DS-260 Unlock Request - {identity['case_no']} - {identity['full_name']}`\n\n"
            "```text\n"
            "Dear Kentucky Consular Center,\n\n"
            "I am writing to respectfully request that my DS-260 Immigrant Visa Electronic Application be unlocked so that I may update critical information (address / interviewing post / personal details).\n\n"
            f"Case Number: {identity['case_no']}\n"
            f"Principal Applicant Name: {identity['full_name']}\n"
            f"Date / Place of Birth: {identity['birth_info']}\n\n"
            f"Reason for Request: {scenario or 'Need to update residential address and interview post details.'}\n\n"
            "Thank you very much for your time and assistance.\n\n"
            "Sincerely,\n"
            f"{identity['full_name']}\n"
            "```"
        )
    if intent == "expedited":
        return (
            "📧 *ABD Konsolosluğu Acil Randevu (Expedited Appointment) Taslağı*\n"
            "• *Platform:* `ustraveldocs.com` -> Request Expedite\n"
            f"• *Konu:* `Request for Expedited Visa Appointment - {identity['full_name']}`\n\n"
            "```text\n"
            "Dear Consular Section,\n\n"
            "I respectfully request an expedited nonimmigrant visa interview appointment due to an urgent, time-sensitive matter supported by official documentation.\n\n"
            f"Applicant Name: {identity['full_name']}\n"
            "DS-160 Confirmation No: [DS-160 NUMARANIZI YAZIN]\n\n"
            f"Urgent Justification: {scenario or 'Time-sensitive academic program start / critical business travel / medical urgency.'}\n\n"
            "Supporting documents (invitation letter / I-20 / medical report) are ready to be uploaded/presented at the interview. Thank you for your consideration.\n\n"
            "Respectfully,\n"
            f"{identity['full_name']}\n"
            "```"
        )
    return (
        "📧 *KCC / Konsolosluk Dosya Taşıma (Case Transfer) Resmi E-Posta Taslağı*\n"
        "• *Alıcı (2NL Öncesi):* `KCCDV@state.gov` _(2NL geldiyse hedef konsolosluk IV birimi)_\n"
        f"• *Subject:* `Case Transfer Request - {identity['case_no']} - {identity['full_name']}`\n\n"
        "```text\n"
        "Dear Kentucky Consular Center / Consular Section,\n\n"
        "I am a Diversity Visa selectee writing to request the transfer of my immigrant visa case to the U.S. Embassy/Consulate in [HEDEF ŞEHİR / ÜLKE], where I currently hold legal residency / long-term status.\n\n"
        f"Case Number: {identity['case_no']}\n"
        f"Principal Applicant Name: {identity['full_name']}\n"
        f"Date / Place of Birth: {identity['birth_info']}\n"
        "Current Processing Post: Ankara, Turkey\n"
        "Requested Processing Post: [HEDEF ŞEHİR / ÜLKE]\n\n"
        f"Legal Basis & Reason: {scenario or 'Legal residency / employment authorization in the requested country (supporting residence permit attached).'}\n\n"
        "Attached please find a copy of my valid residence permit / supporting proof of legal stay. Please let me know if any additional documentation or DS-260 unlock is required.\n\n"
        "Thank you for your assistance.\n\n"
        "Sincerely,\n"
        f"{identity['full_name']}\n"
        "```"
    )


def analyze_transfer_and_build_letter(
    scenario: str,
    profile: Dict[str, Any],
    use_ai: bool = False,
    ai_callable: Optional[Callable[[str], str]] = None,
) -> str:
    """Analyze a transfer/appointment scenario and produce strategic advice + English template."""
    clean_scenario = (scenario or "").strip()
    if not clean_scenario:
        return build_transfer_policy_overview()

    identity = _extract_case_and_identity(profile)
    intent = _detect_transfer_intent(clean_scenario)
    lower = clean_scenario.casefold()

    # Stratejik risk kontrolü
    has_residency_hint = any(
        w in lower for w in ("oturum", "ikamet", "vatandaş", "çalışma izni", "öğrenci", "residence", "permit", "blue card", "vize ile yaşıyorum")
    )
    wants_tourist_transfer = any(
        w in lower for w in ("turist", "vizesiz", "sıra bekleme", "hızlı ülke", "umman", "hong kong", "bangkok", "sırbistan", "gürcistan", "karadağ")
    ) and not has_residency_hint

    strategy_notes = []
    if intent == "transfer":
        if wants_tourist_transfer:
            strategy_notes.append(
                "🚨 *Kritik Risk Uyarısı:* Metninizde hedef ülkede yasal oturum izniniz olduğuna dair bilgi görünmüyor. "
                "2025–2026 Dışişleri Bakanlığı kuralına göre turistik/kısa süreli giriş yapılan ülkelere yapılan "
                "transfer başvuruları çoğunlukla *reddedilmektedir* ve gereksiz zaman kaybettirir. "
                "Eğer o ülkede yasal oturumunuz, çalışma izniniz veya vatandaşlığınız varsa mutlaka dilekçeye kanıtını (ikamet kartı PDF/JPEG) ekleyin."
            )
        elif has_residency_hint:
            strategy_notes.append(
                "🟢 *Güçlü Transfer Zemini:* Belirttiğiniz yasal oturum/ikamet durumu dosya taşıma talebi için geçerli bir gerekçedir. "
                "Dosya KCC'deyse (2NL gelmediyse) önce DS-260 kilidini açtırıp adresinizi güncellemeyi unutmayın."
            )
        else:
            strategy_notes.append(
                "🟡 *Stratejik Hatırlatma:* Başka bir ülkeye dosya taşıma talebinin onaylanması için o ülkede *yasal oturum izni / çalışma izni / vatandaşlık* "
                "veya çok ağır insani/tıbbi zorunluluk belgelenmelidir. Dilekçede bu kanıtı netçe belirtin."
            )
    elif intent == "unlock":
        strategy_notes.append(
            "🔓 *DS-260 Kilidi Açtırma Kuralı:* KCC formu yeniden açtığında tüm sayfaları tek tek kontrol edip *Sign and Submit* yapmalısınız; "
            "aksi halde form 'Incomplete' durumuna düşer ve mülakat sıranız durur!"
        )
    else:
        strategy_notes.append(
            "⚡ *Acil Randevu Kuralı:* Sistemde MRV ücretini ödeyip önce en erken normal randevuyu (örneğin 8-12 ay sonrasına bile olsa) seçmeden "
            "'Expedite Request' (Acil Randevu) butonu aktif olmaz. Mutlaka kanıtlayıcı belge (I-20, davet mektubu, doktor raporu) hazır olmalıdır."
        )

    letter = _build_template_letter(intent, clean_scenario, identity)

    if use_ai and ai_callable is not None:
        try:
            ai_prompt = (
                "Sen kıdemli bir ABD göçmenlik danışmanısın. Kullanıcının şu dosya taşıma / konsolosluk randevu "
                f"durumu için KISA ve NET stratejik yorum yap (maksimum 4 madde):\n"
                f"Durum: {clean_scenario}\n"
                f"Profil Case No: {identity['case_no']}\n"
                "Not: 2025-2026 oturum izni zorunluluğunu ve KCC vs 2NL sonrası Konsolosluk farkını mutlaka gözet."
            )
            ai_insight = (ai_callable(ai_prompt) or "").strip()
            if ai_insight:
                strategy_notes.append(f"🧠 *Danışman Analizi:*\n{ai_insight[:900]}")
        except Exception:
            pass

    lines = [
        "✈️ *Dosya Taşıma & Konsolosluk Strateji Raporu*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        *strategy_notes,
        "",
        letter,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *İpucu:* Taslaktaki `[...]` alanlarını kendi bilgilerinizle doldurup ikamet/destek belgelerinizi PDF veya JPEG olarak ekleyerek gönderin.",
    ]
    return "\n".join(lines)


# ============================================================================
# 2. 360° AMERİKAN VİZESİ UYGUNLUK ANALİZÖRÜ (TÜM ABD VİZE KATEGORİLERİ)
# ============================================================================

def analyze_all_us_visas(profile: Dict[str, Any]) -> str:
    """Assess user profile across all major US immigrant & nonimmigrant visa pathways."""
    facts = profile.get("user_facts", {}) if profile else {}
    job = facts.get("meslek", "").strip()
    edu = facts.get("egitim", "").strip()
    budget_raw = facts.get("butce", "").strip()
    budget_val = parse_numeric_budget(budget_raw)
    english = facts.get("ingilizce", "").strip()
    family = facts.get("medeni_durum", "").strip()

    job_l = job.lower()
    edu_l = edu.lower()
    eng_l = english.lower()

    has_advanced_edu = any(w in edu_l for w in ("yüksek lisans", "master", "doktora", "phd"))
    has_bachelor = "lisans" in edu_l or has_advanced_edu
    is_stem_or_pro = any(
        w in job_l for w in ("yazılım", "mühendis", "veri", "doktor", "akademisyen", "mimar", "hemşire", "finans", "yönetici", "girişimci")
    )

    # 1. DV Lottery
    dv_status = "🟡 Askıda (9. Daire Temyiz Sürecinde)"
    dv_note = "Red Eagle Law davasında 29 Ekim temyiz durdurması sonrası portal bekleniyor; teknik hazırlık (fotoğraf/pasaport) hazır tutulmalı."

    # 2. EB-2 NIW
    if has_advanced_edu or (has_bachelor and is_stem_or_pro):
        niw_score = "🟢 Yüksek Uygunluk"
        niw_note = f"Profiliniz ({job or 'Nitelikli alan'} / {edu or 'Eğitim'}) iş teklifi olmadan doğrudan Green Card sağlayan EB-2 NIW için çok güçlü aday profili sunuyor."
    elif is_stem_or_pro:
        niw_score = "🟡 Orta-Yüksek Uygunluk"
        niw_note = "Alanınızda 5+ yıl ilerleyici deneyim veya ek sertifika/yayınlarla iş teklifsiz EB-2 NIW dosyası kurulabilir."
    else:
        niw_score = "⚪ Ön Değerlendirme Gerekli"
        niw_note = "Lisans + 5 yıl deneyim veya ulusal öneme sahip proje/ticari girişim kanıtlanabilirse başvurulabilir."

    # 3. E-2 Yatırımcı Vizesi
    if budget_val >= 85000:
        e2_score = "🟢 Güçlü Finansal Uygunluk"
        e2_note = f"~${budget_val:,.0f} birikiminiz ABD'de gerçek bir işletme kurup Türkiye anlaşmalı yatırımcı vizesi (E-2) almak için yeterli aralıkta."
    elif budget_val >= 45000:
        e2_score = "🟡 Sınırda / Kısmi Uygunluk"
        e2_note = "Hizmet/danışmanlık veya niş franchise modellerinde sermaye desteğiyle E-2 planlanabilir."
    else:
        e2_score = "🔴 Düşük Sermaye Uygunluğu"
        e2_note = "E-2 için genelde $75K-$100K+ aktif işletme yatırımı gerekir; mevcut bütçenizle çekiliş, istihdam veya eğitim rotaları çok daha rasyoneldir."

    # 4. F-1 / STEM OPT
    if any(w in eng_l for w in ("b2", "c1", "c2", "akıcı", "ileri")) or budget_val >= 25000:
        f1_score = "🟢 Uygun B Planı"
        f1_note = "STEM alanında 1-2 yıllık yüksek lisans ile mezuniyet sonrası 3 yıl yasal çalışma hakkı (STEM OPT) elde edilebilir."
    else:
        f1_score = "🟡 Hazırlık Gerektirir"
        f1_note = "Dil skoru (TOEFL/IELTS) ve ilk yıl eğitim+yaşam maliyeti ($25K+) teminatı gereklidir."

    # 5. B1/B2 Turist/İş Vizesi & 214(b) Analizi
    b1b2_risk = "Düşük/Orta Risk" if (job or has_bachelor) else "Dikkatli Dosya Gerekir"
    b1b2_note = (
        "214(b) maddesi uyarınca vize memuruna Türkiye'deki iş, gelir, aile ve mülk bağlarınızı ikna etmelisiniz. "
        "DS-160 formundaki tutarsızlıklar veya belirsiz seyahat planı ret sebebidir."
    )

    # 6. O-1 / L-1 / H-1B
    work_note = (
        "Uluslararası şirkette 1 yıl çalışıp L-1 transferi almak (kurasız), ödül/basın/yüksek maaşla O-1 almak "
        "veya ABD işveren sponsorluğuyla H-1B'ye başvurmak temel çalışma yollarıdır."
    )

    prof_header = (
        f"👤 *Baz Alınan Profil:* {job or 'Belirtilmedi'} | {edu or 'Eğitim belirtilmedi'} | {budget_raw or 'Bütçe belirtilmedi'}"
        f"{' | ' + family if family else ''}"
    )

    lines = [
        "🏛️ *360° Amerikan Vizesi Uygunluk & Strateji Raporu*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        prof_header,
        "",
        f"1️⃣ *DV Lottery (Green Card Çekilişi):* {dv_status}\n_{dv_note}_\n",
        f"2️⃣ *EB-2 NIW (İş Teklifsiz Doğrudan Green Card):* {niw_score}\n_{niw_note}_\n",
        f"3️⃣ *E-2 Yatırımcı Vizesi (Türk Vatandaşlarına Özel):* {e2_score}\n_{e2_note}_\n",
        f"4️⃣ *F-1 Yüksek Lisans + STEM OPT (3 Yıl Çalışma):* {f1_score}\n_{f1_note}_\n",
        f"5️⃣ *H-1B / L-1 / O-1 Çalışma Vizeleri:* 🔵 *Kariyer Rotası*\n_{work_note}_\n",
        f"6️⃣ *B1/B2 Turistik/Ticari Vize (214b Değerlendirmesi):* {b1b2_risk}\n_{b1b2_note}_",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Sonraki Adım:* Profiliniz eksikse `/profil meslek ...` ve `/profil butce ...` ile güncelleyip raporu yeniden çalıştırabilir, ya da herhangi bir vize türünü sorup detaylı yol haritası isteyebilirsiniz.",
    ]
    return "\n".join(lines)


# ============================================================================
# 3. DS-260 "3 GÖZ KURALI" TUTARLILIK VE RİSK DENETLEYİCİSİ
# ============================================================================

def audit_ds260_consistency(
    profile: Dict[str, Any],
    fields_meta: List[tuple],
    ai_callable: Optional[Callable[[str], str]] = None,
) -> str:
    """Perform a 3-pair-of-eyes consistency check across DS-260 fields, checklist, and user_facts."""
    ds260 = profile.get("ds260", {})
    facts = profile.get("user_facts", {})
    chk = profile.get("checklist", {})

    filled_count = 0
    missing_labels: List[str] = []
    warnings: List[str] = []
    passed_checks: List[str] = []

    for key, label in fields_meta:
        val = (ds260.get(key) or "").strip()
        if not val:
            missing_labels.append(label.split("(")[0].strip())
        else:
            filled_count += 1

    # Kontrol 1: Pasaport isimlerinde Türkçe karakter riski
    full_name = (ds260.get("full_name") or "").strip()
    if full_name:
        if TURKISH_CHARS_PATTERN.search(full_name):
            warnings.append(
                "⚠️ *Türkçe Karakter Riski:* Tam Ad-Soyad alanında Türkçe özel karakter (`ğ, ü, ş, ı, ö, ç`) tespit edildi. "
                "DS-260 formunda pasaportun altındaki MRZ (`P<TUR...`) satırındaki gibi *yalnızca İngilizce harfler* kullanılmalıdır!"
            )
        elif len(full_name.split()) < 2:
            warnings.append("⚠️ *Ad-Soyad Eksikliği:* Pasaporttaki tüm ad ve soyadınızı tam olarak yazmalısınız.")
        else:
            passed_checks.append("✅ Pasaport adı İngilizce karakter formatına uygun.")

    # Kontrol 2: Pasaport numarası ve tarih formatı
    passport_no = (ds260.get("passport_no") or "").strip()
    if passport_no:
        if not re.search(r"[A-Za-z]\d{7,8}|\d{7,9}", passport_no):
            warnings.append("⚠️ *Pasaport Numarası Kontrolü:* Pasaport no formatı standart görünmüyor (ör. `U12345678`); harf ve rakamları birebir teyit edin.")
        if not chk.get("passport_valid"):
            warnings.append("⚠️ *Checklist Uyumsuzluğu:* DS-260'a pasaport bilgisi girilmiş ancak checklist'te 'Geçerli pasaport hazır' henüz işaretlenmemiş.")

    # Kontrol 3: Aile & Medeni durum çapraz tutarlılık
    marital_ds = (ds260.get("marital_dependents") or "").lower()
    marital_facts = (facts.get("medeni_durum") or "").lower()
    if marital_ds and marital_facts:
        if ("evli" in marital_facts and "bekar" in marital_ds) or ("bekar" in marital_facts and "evli" in marital_ds):
            warnings.append(
                "🚨 *Kritik Çapraz Çelişki:* Profil hafızanızdaki medeni durum ile DS-260 alanındaki bilgi çelişiyor! "
                "Yanlış medeni durum beyanı doğrudan vize reddi (diskalifiye) sebebidir."
            )
        else:
            passed_checks.append("✅ Medeni durum verileri profilinizle tutarlı.")

    # Kontrol 4: Adres & İş boşluğu (gap) hatırlatması
    addr = (ds260.get("address_history") or "").strip()
    work = (ds260.get("work_history") or "").strip()
    if addr and len(addr) < 25:
        warnings.append("🟡 *Adres Geçmişi Çok Kısa:* 16 yaşından günümüze kadar hiçbir ay boşluğu bırakmadan şehir/ilçe tarihlerini listelediğinizden emin olun.")
    if work and len(work) < 20:
        warnings.append("🟡 *İş Geçmişi Çok Kısa:* Son 10 yılda çalışmadığınız/okuduğunuz dönemler varsa 'Unemployed' veya 'Student' olarak belirtmeniz 221(g) riskini önler.")

    # Kontrol 5: Sosyal Medya 5 yıllık zorunluluk
    social = (ds260.get("social_media") or "").strip()
    if not social:
        warnings.append("⚠️ *Sosyal Medya Alanı Boş:* Son 5 yılda kullandığınız tüm platform ve kullanıcı adlarını eksiksiz bildirmek zorunludur (DS-5535 ek güvenlik formu riskini azaltır).")
    else:
        passed_checks.append("✅ Son 5 yıllık sosyal medya beyanı girilmiş.")

    ai_review = ""
    if ai_callable is not None and filled_count >= 2:
        try:
            filled_dump = "\n".join(
                f"- {label}: {ds260.get(k)}"
                for k, label in fields_meta
                if (ds260.get(k) or "").strip()
            )
            prompt = (
                "Sen kıdemli bir ABD göçmenlik danışmanısın ('3 Göz Kuralı' denetçisi). "
                "Aşağıdaki DS-260 ön-kayıt verilerini konsolosluk vize memuru gözüyle incele; "
                "varsa tarih boşluğu, 221(g) riski veya düzeltilmesi gereken en önemli 2-3 noktayı kısaca yaz:\n\n"
                f"{filled_dump}"
            )
            ai_review = (ai_callable(prompt) or "").strip()
        except Exception:
            ai_review = ""

    lines = [
        "🔍 *DS-260 '3 Göz Kuralı' Tutarlılık & Risk Denetimi*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 *Doluluk Oranı:* *{filled_count} / {len(fields_meta)}* alan hazır",
    ]

    if passed_checks:
        lines.extend(["", *passed_checks])

    if warnings:
        lines.extend(["", "🚨 *TESPİT EDİLEN RİSKLER VE UYARILAR:*", *warnings])
    elif filled_count > 0:
        lines.extend(["", "🟢 *Kayıtlı alanlarda belirgin bir format veya çapraz çelişki tespit edilmedi.*"])

    if missing_labels:
        lines.extend([
            "",
            f"⬜ *Tamamlanması Gereken Alanlar ({len(missing_labels)}):*",
            "• " + "\n• ".join(missing_labels[:5]) + ("\n• _...ve diğerleri_" if len(missing_labels) > 5 else ""),
        ])

    if ai_review:
        lines.extend(["", "🧠 *AI Konsolosluk Ön İncelemesi:*", ai_review[:1100]])

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Altın Kural:* DS-260'a girdiğiniz her tarih (okul, SGK işi, adres, evlilik), mülakatta sunacağınız Formül A/B, SGK dökümü ve diplomalarla gün/ay/yıl olarak %100 örtüşmelidir.",
    ])
    return "\n".join(lines)


# ============================================================================
# 4. PROAKTİF KCC / KONSOLOSLUK YAZIŞMA MOTORU ("ONLARA ŞU ŞEKİLDE SÖYLEYELİM")
# ============================================================================

def generate_proactive_case_emails(
    kind: str,
    profile: Dict[str, Any],
    extra_note: str = "",
) -> str:
    """Generate ready-to-send official English correspondence for KCC, US Embassies, and Consular Officers."""
    identity = _extract_case_and_identity(profile)
    facts = (profile or {}).get("user_facts", {}) if profile else {}
    job = facts.get("meslek", "").strip() or "Qualified Professional"
    edu = facts.get("egitim", "").strip() or "University Degree"
    budget_raw = facts.get("butce", "").strip() or "$20,000+"
    target_loc = facts.get("hedef_lokasyon", "").strip() or "United States"
    k = (kind or "kcc_status").strip().lower()

    if k == "kcc_status":
        return (
            "📧 *KCC Dosya Durumu & DS-260 İşleme Teyidi Maili (`KCCDV@state.gov`)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🧠 *Neden Gönderiyoruz? (Senin Yerine Düşündüm):*\n"
            "Sıra numaran Vize Bülteni'nde 'Current' olduğu sabah tek bir gün bile kaybetmeden mülakat randevu mektubunun (2NL) "
            "atanabilmesi için KCC'deki DS-260 formunun *'Processed / Documentarily Qualified'* (incelenmiş ve mülakata hazır) "
            "statüsünde olması şarttır. KCC'ye şu şekilde yazarak dosyamızın hazır olduğunu teyit edelim:\n\n"
            "• *Alıcı:* `KCCDV@state.gov`\n"
            f"• *Subject:* `Case Status & DS-260 Readiness Inquiry - {identity['case_no']} - {identity['full_name']}`\n\n"
            "```text\n"
            "Dear Kentucky Consular Center,\n\n"
            "I am a Diversity Visa selectee writing to kindly confirm the processing status and interview readiness of my immigrant visa case.\n\n"
            f"Case Number: {identity['case_no']}\n"
            f"Principal Applicant Name: {identity['full_name']}\n"
            f"Date / Place of Birth: {identity['birth_info']}\n\n"
            "Given our case rank and the strict September 30 fiscal year deadline, I want to ensure that our submitted DS-260 Immigrant Visa Electronic Application has been fully reviewed and processed, and that there are no pending administrative holds Preventing immediate interview scheduling at the U.S. Embassy once our case number becomes current in the Visa Bulletin.\n\n"
            "Please let me know if our case is currently marked as ready for scheduling, or if any further action is required from our side.\n\n"
            "Thank you very much for your time and assistance.\n\n"
            "Sincerely,\n"
            f"{identity['full_name']}\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Kritik Taktik:* KCC'den _'Your forms have been received and processed / Your case is ready to be scheduled'_ "
            "yanıtı geldiğinde dosyanız yeşil ışık almış demektir!"
        )

    if k == "urgent_embassy":
        return (
            "🚨 *Dar Takvim / 30 Eylül Mali Yıl Sınırı Acil Randevu Maili (Konsolosluk & KCC)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🧠 *Neden Gönderiyoruz? (Senin Yerine Düşündüm):*\n"
            "Sıra numaran yüksekse veya Vize Bülteni'nde 'Current' olduğun halde yaz sonuna (Temmuz-Eylül) girilmiş ve hala 2NL gelmemişse, "
            "30 Eylül gece yarısı tüm DV vize hakları yasal olarak sıfırlanır. Süre daraldığında pasif beklemeyip "
            "hem KCC'ye hem de ABD Ankara Büyükelçiliği Göçmen Vize birimine (Immigrant Visa Navigator) şu şekilde acil mülakat talebi yazmalıyız:\n\n"
            "• *Alıcı:* `KCCDV@state.gov` ve Ankara ABD Büyükelçiliği IV Birimi (`AnkaraIV` / Resmi Navigator)\n"
            f"• *Subject:* `URGENT: Fiscal Year Expiration Risk - Request for Prompt DV Interview Scheduling - {identity['case_no']}`\n\n"
            "```text\n"
            "Dear Consular Section / Kentucky Consular Center,\n\n"
            "I am a Diversity Visa selectee whose case number is currently eligible for interview scheduling under the Visa Bulletin. I am writing to respectfully request urgent interview scheduling due to the approaching September 30 statutory fiscal year deadline.\n\n"
            f"Case Number: {identity['case_no']}\n"
            f"Principal Applicant Name: {identity['full_name']}\n"
            f"Date / Place of Birth: {identity['birth_info']}\n"
            "Interviewing Post: U.S. Embassy Ankara, Turkey\n\n"
            "Our DS-260 application has been submitted and all required civil, police, and financial documents are completely prepared. We are ready to complete the medical examination and attend an interview at the shortest possible notice so that our Diversity Visa opportunity is not lost prior to the September 30 cutoff.\n\n"
            "Thank you deeply for your attention and assistance with this time-sensitive request.\n\n"
            "Respectfully,\n"
            f"{identity['full_name']}\n"
            "```\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Kritik Taktik:* Bu maili numaranız Vize Bülteni'nde 'Current' (Cut-off altında) olduğu andan itibaren gönderebilirsiniz."
        )

    if k == "ap_221g":
        return (
            "🛡️ *221(g) İdari İşlem (Administrative Processing) Takip & Dosya Hızlandırma Maili*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🧠 *Neden Gönderiyoruz? (Senin Yerine Düşündüm):*\n"
            "Mülakat sonrası memur ek güvenlik soruşturması (özellikle yazılım, mühendislik, akademi, savunma/TAL alanlarında) veya "
            "evrak kontrolü için 221(g) verdiyse, 30 Eylül mali yıl sonundan önce işlemin tamamlanması şarttır. "
            "Konsolosluğa hem istenen bilgileri/CV'yi sunmak hem de 30 Eylül yasal sınırını nazikçe hatırlatmak için onlara şu şekilde söyleyelim:\n\n"
            "• *Alıcı:* Mülakata girdiğiniz ABD Konsolosluğu IV Birimi (Ankara IV Navigator / İlgili Post)\n"
            f"• *Subject:* `221(g) Administrative Processing Follow-Up & Fiscal Deadline - {identity['case_no']} - {identity['full_name']}`\n\n"
            "```text\n"
            "Dear Immigrant Visa Unit,\n\n"
            "I am writing to respectfully follow up on my Diversity Visa application, which was placed under Section 221(g) administrative processing following my consular interview.\n\n"
            f"Case Number: {identity['case_no']}\n"
            f"Principal Applicant Name: {identity['full_name']}\n"
            f"Date / Place of Birth: {identity['birth_info']}\n\n"
            "Because Diversity Visa issuance is strictly subject to the September 30 statutory fiscal year deadline, I wanted to kindly inquire if any additional documentation, updated medical records, or clarification regarding my professional background (detailed CV / publication list) would assist in concluding the review.\n\n"
            "We remain ready to provide any requested document or passport immediately upon notification.\n\n"
            "Thank you very much for your time, service, and consideration.\n\n"
            "Respectfully,\n"
            f"{identity['full_name']}\n"
            "```"
        )

    if k == "public_charge":
        return (
            "💵 *Mülakat Memuru İçin Hazır Finansal & Kariyer Güvence Özeti (Public Charge Cover Letter)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🧠 *Neden Hazırladık? (Senin Yerine Düşündüm):*\n"
            "Konsolosluk mülakatında vize memurunun en çok dikkat ettiği nokta *INA 212(a)(4) Public Charge* (ABD'ye gidince kamu yükü olmama) kriteridir. "
            "Banka hesap dökümlerinin, diplomalarının ve iş planının en üstüne koyarak memura uzatabileceğin "
            "profesyonel İngilizce *Finansal & İstihdam Taahhüt Özeti*: \n\n"
            "```text\n"
            "MEMORANDUM OF FINANCIAL SELF-SUFFICIENCY & EMPLOYABILITY PLAN\n"
            "To: Consular Officer, Immigrant Visa Unit\n"
            f"From: {identity['full_name']} (Case Number: {identity['case_no']})\n\n"
            "1. PROFESSIONAL & EDUCATIONAL QUALIFICATION:\n"
            f"   - Current Profession / Field: {job}\n"
            f"   - Education Level: {edu}\n"
            f"   - Target U.S. Destination: {target_loc}\n\n"
            "2. LIQUID FINANCIAL ASSETS & INITIAL RELOCATION FUNDS:\n"
            f"   - Immediately Available Liquid Savings: {budget_raw} (official bank statements attached)\n"
            "   - Additional Support / Assets: Debt-free relocation budget covering initial housing, transportation, and living expenses for at least 6 months.\n\n"
            "3. IMMEDIATE U.S. EMPLOYMENT & INTEGRATION ROADMAP:\n"
            "   - Active preparation for U.S. job market applications in my professional sector immediately upon arrival.\n"
            "   - Full health insurance and private financial coverage without any reliance on U.S. public assistance.\n\n"
            f"Signed: {identity['full_name']}\n"
            "```"
        )

    if k in ("unlock", "transfer", "expedited"):
        return analyze_transfer_and_build_letter(extra_note or k, profile)

    return analyze_transfer_and_build_letter(extra_note or "transfer", profile)


# ============================================================================
# 5. "BENİM YERİNE DÜŞÜN" 360° PROAKTİF SENARYO & AKSİYON MOTORU
# ============================================================================

def build_proactive_action_plan(profile: Dict[str, Any]) -> str:
    """Think ahead on behalf of the user by cross-analyzing Case Number, DS-260, Checklist, Career, and Budget."""
    facts = (profile or {}).get("user_facts", {}) if profile else {}
    ds260 = (profile or {}).get("ds260", {}) if profile else {}
    chk = (profile or {}).get("checklist", {}) if profile else {}

    case_raw = (facts.get("case_number") or "").strip()
    job = (facts.get("meslek") or "").strip()
    edu = (facts.get("egitim") or "").strip()
    budget_raw = (facts.get("butce") or "").strip()
    budget_val = parse_numeric_budget(budget_raw)
    family = (facts.get("medeni_durum") or "").strip()
    target_loc = (facts.get("hedef_lokasyon") or "").strip()

    filled_ds = sum(1 for v in ds260.values() if v and str(v).strip())
    done_chk = sum(1 for v in chk.values() if v)

    bottlenecks: List[str] = []
    scenarios: List[str] = []
    immediate_moves: List[str] = []
    selected_email_kind = "kcc_status"

    # 1. Case Number Analizi ve Dar Takvim Tespiti
    if case_raw:
        c_info = analyze_case_number(case_raw, profile)
        if c_info.get("valid"):
            rank = c_info["rank"]
            tier_code = c_info.get("tier_code", "medium")
            bottlenecks.append(
                f"🔢 *Sıra Numarası Konumu (`{c_info['raw']}` — #{rank:,}):* {c_info['tier']} — Tahmini pencere: *{c_info['projected_period']}*."
            )
            scenarios.extend(c_info.get("scenarios", [])[:3])
            if tier_code in ("high", "very_high"):
                immediate_moves.append(
                    "🚨 *Yüksek Sıra / Dar Takvim Hamlesi:* Numaran yüksek dilimde olduğu için DS-260 formunu derhal tamamlayıp KCC'ye (`KCCDV@state.gov`) dosya hazırlık (Documentarily Qualified) teyit maili atmalıyız."
                )
                immediate_moves.append(
                    "✈️ *Konsolosluk B Planı:* Ankara Konsolosluğu yaz randevu yoğunluğuna karşı yasal oturum/çalışma/öğrenci izni imkanın olan bir ülke varsa dosya taşıma (`/dosya_tasima`) veya Current olunca Acil Randevu talebini hazır tutacağız."
                )
                selected_email_kind = "kcc_status"
            else:
                immediate_moves.append(
                    "📧 *KCC İşleme Teyidi:* Sıra numaran iyi; ancak DS-260 KCC'de işlenmezse 2NL gecikir. KCC'ye dosya durum teyit maili atarak sıranı garantiye alalım."
                )
                selected_email_kind = "kcc_status"
    else:
        bottlenecks.append(
            "🔢 *Case Number Henüz Girilmedi:* Sıra numaranı `/case 2027EU000XXXXX` şeklinde girdiğinde veya sohbete yazdığında sana özel mülakat ayı ve KCC mektup stratejisini anında kuracağım."
        )
        scenarios.extend([
            "🟢 *Senaryo 1 (Erken Hazırlık Avantajı):* DV-2027 mahkeme süreci (9. Daire temyizi) sonuçlanıp portal açıldığında veya sonuçlar açıklandığında tüm DS-260 verilerin hazır olduğu için ilk 48 saatte başvurunu tamamlarsın.",
            "🟡 *Senaryo 2 (Yüksek Sıra Numarası Çıkması Durumu):* Eğer çekilişte yüksek bir Case Number (ör. EU25000+) gelirse, KCC'ye ilk gün DS-260 gönderip dosya hazırlık teyit maili atarak ön sıraya geçeceğiz.",
            "🔵 *Senaryo 3 (Paralel B Planı Vizesi):* Çekiliş takviminden bağımsız olarak meslek ve bütçe profiline uygun ABD vize rotalarını (EB-2 NIW / F-1 / E-2 / B1-B2) eşzamanlı ilerletebiliriz.",
        ])

    # 2. DS-260 ve Evrak Darboğazı
    if filled_ds < 7:
        bottlenecks.append(
            f"📝 *DS-260 Veri Eksikliği ({filled_ds}/10 alan dolu):* 16 yaşından itibaren adres ve son 10 yıllık SGK iş geçmişinde boşluk olması KCC incelemesini yavaşlatır."
        )
        immediate_moves.append(
            "📝 *DS-260 Simülatörü & 3 Göz Denetimi:* `/ds260` üzerinden eksik alanları doldurup '3 Göz Kuralı' denetimiyle Türkçe karakter ve tarih çelişkilerini sıfırla."
        )
    else:
        bottlenecks.append(f"✅ *DS-260 Hazırlığı Güçlü ({filled_ds}/10 alan dolu):* Form verilerin KCC gönderimine büyük ölçüde hazır.")

    # 3. Meslek & 221(g) TAL (Technology Alert List) Riski + EB-2 NIW Fırsatı
    job_l = job.lower()
    edu_l = edu.lower()
    if any(w in job_l for w in ("yazılım", "mühendis", "veri", "siber", "yapay zeka", "kimya", "fizik", "biyoloji", "savunma", "akademisyen", "ar-ge")):
        bottlenecks.append(
            f"🛡️ *Mesleki 221(g) (TAL) Güvenlik İncelemesi Riski ({job}):* Teknik/mühendislik alanındaki adaylara mülakatta sıkça CV sorulur ve 221(g) idari işlem verilebilir."
        )
        immediate_moves.append(
            "📄 *221(g) Kalkanı:* Mülakata giderken yanına mutlaka *İngilizce detaylı CV, güncel iş tanımı ve varsa yayın/proje listesi* al; bu hazırlık haftalar süren 221(g) idari işlemini önler!"
        )
        if any(w in edu_l for w in ("yüksek lisans", "master", "doktora", "phd", "lisans")):
            immediate_moves.append(
                "🚀 *B Planı Fırsatı (EB-2 NIW):* Mühendislik/uzmanlık profilin iş teklifsiz doğrudan Green Card veren *EB-2 NIW* için çok uygun (`/vize_analiz`)."
            )

    # 4. Bütçe & Public Charge (Kamu Yükü) Kalkanı
    is_fam = "evli" in family.lower() or "çocuk" in family.lower()
    min_safe_budget = 22000 if is_fam else 12000
    if budget_val > 0 and budget_val < min_safe_budget:
        bottlenecks.append(
            f"💵 *Public Charge (Finansal Teminat) Sınırda (${budget_val:,.0f}):* {'Aileli' if is_fam else 'Tek kişi'} başvuru için konsolosluk memuru ek teminat veya ABD'den Form I-134 sponsoru görmek isteyebilir."
        )
        immediate_moves.append(
            "💵 *Public Charge Dosyası:* Mülakata kadar likit banka bakiyesini güçlendir, varsa araç/tapu değerlemelerini ekle ve aşağıdaki *Public Charge Finansal Taahhüt Özeti*ni dosyana koy."
        )
    elif budget_val == 0:
        bottlenecks.append(
            "💵 *Bütçe Kaydı Eksik:* `/profil butce 20000$` şeklinde birikimini kaydettiğinde sana özel eyalet runway ve Public Charge hesabını çıkaracağım."
        )
    else:
        bottlenecks.append(
            f"🟢 *Finansal Güvence (${budget_val:,.0f}):* Birikimin mülakatta Public Charge şüphesini aşmak için güçlü bir zeminde."
        )

    email_preview = generate_proactive_case_emails(selected_email_kind, profile)

    lines = [
        "🧠 *SENİN YERİNE DÜŞÜNDÜM: 360° PROAKTİF STRATEJİ & AKSİYON PLANI*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"👤 *Profil Özeti:* {job or 'Meslek belirtilmedi'} | {family or 'Medeni durum belirtilmedi'} | {budget_raw or 'Bütçe belirtilmedi'} | Hedef: {target_loc or 'Belirtilmedi'} | Checklist: {done_chk}/12",
        "",
        "🔍 *1. ŞU ANKİ KRİTİK TESPİTLERİM & DARBOĞAZ ANALİZİ:*",
        *[f"• {b}" for b in bottlenecks],
        "",
        "🔮 *2. SENİN YERİNE KURDUĞUM 3 OLASI SENARYO:*",
        *scenarios,
        "",
        "⚡ *3. HEMEN ŞİMDİ ATACAĞIMIZ SOMUT ADIMLAR:*",
        *[f"{idx}. {m}" for idx, m in enumerate(immediate_moves, 1)],
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        email_preview,
    ]
    return "\n".join(lines)
