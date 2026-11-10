"""Comprehensive Strategic Relocation, Case Analysis, and Immigration Intelligence.

Provides deep analytics for:
1. Relocation & Living Cost Calculator (Runway & Public Charge Risk)
2. US States & Metros Comparison (Taxes, Rents, Salaries, Turkish Community)
3. DV Case Number & Visa Bulletin Analyzer (Historical Cutoffs & Projected Timelines)
4. 360° Green Card & DS-260 Readiness & Risk Audit (Score / 100)
5. Alternative US Visa Routes (Plan B: EB-2 NIW, O-1, H-1B, L-1, F-1 STEM OPT, E-2)
6. Immigration & Green Card Glossary (CEAC, 2NL, 221(g), KCC, Public Charge, etc.)
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Tuple

# ============================================================================
# 1. YAŞAM MALİYETİ & RUNWAY HESAPLAYICI (COST OF LIVING & RUNWAY CALCULATOR)
# ============================================================================

STATE_COST_INDEX: Dict[str, Dict[str, Any]] = {
    "texas": {
        "name": "Texas (Austin / Dallas / Houston)",
        "tax_rate": "0% (Eyalet Gelir Vergisi Yok)",
        "rent_1br": 1450,
        "rent_2br": 1950,
        "monthly_living_single": 2800,
        "monthly_living_family": 4800,
        "car_required": True,
        "min_safe_budget_single": 15000,
        "min_safe_budget_family": 25000,
    },
    "california": {
        "name": "California (Silicon Valley / LA / San Diego)",
        "tax_rate": "%1 - %13.3 (Yüksek Eyalet Vergisi)",
        "rent_1br": 2350,
        "rent_2br": 3200,
        "monthly_living_single": 4100,
        "monthly_living_family": 6900,
        "car_required": True,
        "min_safe_budget_single": 22000,
        "min_safe_budget_family": 36000,
    },
    "florida": {
        "name": "Florida (Miami / Orlando / Tampa)",
        "tax_rate": "0% (Eyalet Gelir Vergisi Yok)",
        "rent_1br": 1750,
        "rent_2br": 2350,
        "monthly_living_single": 3100,
        "monthly_living_family": 5200,
        "car_required": True,
        "min_safe_budget_single": 16000,
        "min_safe_budget_family": 27000,
    },
    "washington": {
        "name": "Washington (Seattle / Bellevue)",
        "tax_rate": "0% (Eyalet Gelir Vergisi Yok)",
        "rent_1br": 2050,
        "rent_2br": 2800,
        "monthly_living_single": 3600,
        "monthly_living_family": 6000,
        "car_required": True,
        "min_safe_budget_single": 19000,
        "min_safe_budget_family": 31000,
    },
    "new_york": {
        "name": "New York (NYC / Brooklyn / Queens)",
        "tax_rate": "%4 - %10.9 (Eyalet + Şehir Gelir Vergisi)",
        "rent_1br": 2600,
        "rent_2br": 3500,
        "monthly_living_single": 3900,
        "monthly_living_family": 6500,
        "car_required": False,  # Toplu taşıma yeterli
        "min_safe_budget_single": 20000,
        "min_safe_budget_family": 34000,
    },
    "north_carolina": {
        "name": "North Carolina (Raleigh / Charlotte)",
        "tax_rate": "%4.5 (Sabit Düz Vergi)",
        "rent_1br": 1350,
        "rent_2br": 1750,
        "monthly_living_single": 2600,
        "monthly_living_family": 4400,
        "car_required": True,
        "min_safe_budget_single": 14000,
        "min_safe_budget_family": 23000,
    },
    "illinois": {
        "name": "Illinois (Chicago)",
        "tax_rate": "%4.95 (Sabit Gelir Vergisi)",
        "rent_1br": 1700,
        "rent_2br": 2300,
        "monthly_living_single": 3100,
        "monthly_living_family": 5100,
        "car_required": False,  # Şehir içi CTA metrosu
        "min_safe_budget_single": 16000,
        "min_safe_budget_family": 26000,
    },
    "massachusetts": {
        "name": "Massachusetts (Boston / Cambridge)",
        "tax_rate": "%5 (Sabit Gelir Vergisi)",
        "rent_1br": 2400,
        "rent_2br": 3100,
        "monthly_living_single": 3800,
        "monthly_living_family": 6300,
        "car_required": False,  # MBTA metrosu var
        "min_safe_budget_single": 20000,
        "min_safe_budget_family": 33000,
    },
}


def parse_numeric_budget(budget_input: Any) -> float:
    """Parse numeric dollar value from string like '$25,000', '20 bin dolar', '15000'."""
    if isinstance(budget_input, (int, float)):
        return float(budget_input)
    if not budget_input or not isinstance(budget_input, str):
        return 0.0

    raw = budget_input.lower().replace(",", "").replace(".", "").strip()
    # Check for 'bin' or 'k'
    multiplier = 1.0
    if "bin" in raw or "k" in raw:
        multiplier = 1000.0

    digits = re.findall(r"\d+", raw)
    if not digits:
        return 0.0

    val = float(digits[0])
    # If user wrote '25' and didn't specify thousands, but wrote 'bin'
    if multiplier == 1000.0 and val < 1000:
        val *= 1000.0
    return val


def calculate_relocation_budget(
    budget_raw: Any,
    state_key: str = "texas",
    is_family: bool = False,
    family_members: int = 1,
) -> Dict[str, Any]:
    """Calculate detailed relocation costs, burn rate, runway, and Public Charge safety."""
    budget = parse_numeric_budget(budget_raw)
    state_key_norm = state_key.lower().replace(" ", "_").strip()
    if state_key_norm not in STATE_COST_INDEX:
        state_key_norm = "texas"
    info = STATE_COST_INDEX[state_key_norm]

    # Kişi sayısı
    num_people = max(family_members, (3 if is_family else 1))

    # Sabit İlk Taşınma Masrafları (One-time startup costs)
    flight_cost = num_people * 1100  # Uçak bileti tek yön
    medical_and_uscis = num_people * 570  # Sağlık raporu ($350) + USCIS Immigrant Fee ($220)
    rent_deposit = info["rent_2br" if is_family else "rent_1br"] * 2  # İlk ay + Güvence depozitosu
    car_downpayment = 4500 if info["car_required"] else 0  # Başlangıç aracı veya depozito
    home_furnishing = 2500 if is_family else 1500  # Temel ev eşyası / mutfak / yatak

    total_startup_cost = flight_cost + medical_and_uscis + rent_deposit + car_downpayment + home_furnishing

    # Aylık Yaşam Maliyeti (Burn rate)
    monthly_burn = info["monthly_living_family" if is_family else "monthly_living_single"]

    # Kalan birikim ve Runway (ay)
    remaining_cash = max(0.0, budget - total_startup_cost)
    runway_months = remaining_cash / monthly_burn if monthly_burn > 0 and budget > total_startup_cost else 0.0

    # Public Charge Risk Değerlendirmesi
    min_safe = info["min_safe_budget_family" if is_family else "min_safe_budget_single"]
    if budget >= min_safe:
        risk_level = "Düşük / Güvenli ✅"
        risk_color = "🟢"
        risk_notes = "Konsolosluk mülakatında Public Charge (kamu yükü) riski bulunmuyor. Birikiminiz ilk 3-6 ay için yeterli."
    elif budget >= (min_safe * 0.65):
        risk_level = "Orta Risk ⚠️"
        risk_color = "🟡"
        risk_notes = "Bütçeniz yeterli ancak dar. Ek tedbir olarak ABD'den Form I-134 (Affidavit of Support) sponsoru hazır bulundurmanız faydalı olur."
    else:
        risk_level = "Yüksek Risk 🚨"
        risk_color = "🔴"
        risk_notes = "Mülakatta vize memuru geçiminizi nasıl sağlayacağınızı sorgulayabilir. Güçlü bir ABD sponsoru (I-134) veya iş teklifi mektubu şarttır."

    return {
        "budget": budget,
        "state_name": info["name"],
        "tax_rate": info["tax_rate"],
        "num_people": num_people,
        "is_family": is_family,
        "total_startup_cost": total_startup_cost,
        "startup_breakdown": {
            "flight_cost": flight_cost,
            "medical_and_uscis": medical_and_uscis,
            "rent_deposit": rent_deposit,
            "car_downpayment": car_downpayment,
            "home_furnishing": home_furnishing,
        },
        "monthly_burn": monthly_burn,
        "remaining_cash": remaining_cash,
        "runway_months": round(runway_months, 1),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_notes": risk_notes,
    }


def format_runway_report(calc: Dict[str, Any]) -> str:
    """Format the calculation result into an actionable Telegram Markdown view."""
    b = calc["budget"]
    f = "Aile (3 Kişi)" if calc["is_family"] else f"{calc['num_people']} Kişi"
    lines = [
        f"💵 *ABD Taşınma & Yaşam Maliyeti / Runway Analizi*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📍 *Hedef Eyalet:* {calc['state_name']}",
        f"💰 *Mevcut Birikim:* ${b:,.0f} | *Kadro:* {f}",
        f"🏛️ *Vergi Durumu:* {calc['tax_rate']}",
        "",
        "🛫 *BAŞLANGIÇ & YERLEŞİM GİDERLERİ (Tek Seferlik):*",
        f"• Uçak Biletleri: ~${calc['startup_breakdown']['flight_cost']:,}",
        f"• Sağlık Raporu & USCIS Harcı: ~${calc['startup_breakdown']['medical_and_uscis']:,}",
        f"• İlk Kira + Depozito: ~${calc['startup_breakdown']['rent_deposit']:,}",
        f"• Araç / Ulaşım Başlangıcı: ~${calc['startup_breakdown']['car_downpayment']:,}",
        f"• Temel Ev Eşyaları & Kurulum: ~${calc['startup_breakdown']['home_furnishing']:,}",
        f"👉 *Toplam Başlangıç Gideri:* *${calc['total_startup_cost']:,}*",
        "",
        "📊 *AYLIK GİDER & RUNWAY (İŞ BULMA PAYI):*",
        f"• Tahmini Aylık Yaşam Gideri: *${calc['monthly_burn']:,} / ay*",
        f"• Yerleşim Sonrası Kalan Nakit: *${calc['remaining_cash']:,.0f}*",
        f"• ⏱️ *Güvenli Dayanma Süresi (Runway):* *{calc['runway_months']} Ay*",
        "",
        f"{calc['risk_color']} *Public Charge (Kamu Yükü) Değerlendirmesi:* *{calc['risk_level']}*",
        f"_{calc['risk_notes']}_",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Koçun Stratejik Önerisi:* İlk 60 gün kredi geçmişiniz (Credit Score) olmadığı için ev kiralarken 2-3 kira depozito istenebilir. İlk hafta bir ABD bankasında secured kredi kartı açtırarak credit score inşasına hemen başlayın.",
    ]
    return "\n".join(lines)


# ============================================================================
# 2. EYALET VE ŞEHİR KARŞILAŞTIRMA MOTORU (STATE & METRO COMPARATOR)
# ============================================================================

STATE_DETAILS: Dict[str, Dict[str, Any]] = {
    "texas": {
        "title": "Texas (Austin, Dallas, Houston)",
        "income_tax": "%0 (Eyalet vergisi yok)",
        "sales_tax": "%6.25 - %8.25",
        "rent_1br": "$1,350 - $1,650",
        "tech_salary": "$115,000 - $155,000",
        "nurse_salary": "$80,000 - $105,000",
        "climate": "Sıcak ve güneşli; yazları 38°C+ nemli/kuru",
        "car": "Zorunlu 🚗 (Şehirler çok geniş)",
        "turkish_community": "Geniş ve örgütlü (Houston & Dallas Türk dernekleri, THY direkt uçuşu)",
        "pros": "Vergi avantajı, teknoloji/enerji/sağlık iş fırsatları, görece uygun konut, dinamik ekonomi.",
        "cons": "Yüksek emlak vergisi (ev alırken), toplu taşıma yok, aşırı yaz sıcakları.",
    },
    "california": {
        "title": "California (Silicon Valley, Los Angeles, San Diego)",
        "income_tax": "%1 - %13.3 (En yüksek eyalet vergisi)",
        "sales_tax": "%7.25 - %10.5",
        "rent_1br": "$2,200 - $3,000",
        "tech_salary": "$150,000 - $220,000+",
        "nurse_salary": "$110,000 - $155,000",
        "climate": "Akdeniz iklimi; yıl boyu ılıman, harika sahil ve doğa",
        "car": "Genellikle gerekli 🚗 (SF merkez hariç)",
        "turkish_community": "Çok yoğun (Silikon Vadisi Türk tech ağı, LA Türk festivali, THY direkt uçuş)",
        "pros": "Dünya teknoloji/girişimcilik merkezi, en yüksek maaşlar, mükemmel iklim ve yaşam kalitesi.",
        "cons": "Aşırı yüksek ev kiraları ve yaşam maliyeti, yüksek gelir ve benzin vergileri.",
    },
    "florida": {
        "title": "Florida (Miami, Orlando, Tampa)",
        "income_tax": "%0 (Eyalet vergisi yok)",
        "sales_tax": "%6.0 - %7.5",
        "rent_1br": "$1,600 - $2,200",
        "tech_salary": "$105,000 - $140,000",
        "nurse_salary": "$75,000 - $95,000",
        "climate": "Tropikal / Sıcak; kışlar ılık, yazlar nemli ve fırtınalı",
        "car": "Zorunlu 🚗",
        "turkish_community": "Hızla büyüyen topluluk (Miami & Orlando Türk restoranları, THY direkt uçuş)",
        "pros": "Gelir vergisi yok, kışın bile sıcak sahil yaşamı, turizm/finans/lojistik canlılığı.",
        "cons": "Yazları yüksek nem ve kasırga sezonu, yükselen ev ve araba sigortası primleri.",
    },
    "washington": {
        "title": "Washington (Seattle, Bellevue, Redmond)",
        "income_tax": "%0 (Eyalet gelir vergisi yok)",
        "sales_tax": "%6.5 - %10.25",
        "rent_1br": "$1,900 - $2,400",
        "tech_salary": "$145,000 - $200,000+",
        "nurse_salary": "$95,000 - $130,000",
        "climate": "Ilıman ama çok yağmurlu ve kapalı (Ekim-Mayıs arası)",
        "car": "Şehir içinde hafif raylı sistem var, genel olarak araba faydalı",
        "turkish_community": "Kuvvetli profesyonel ağ (Microsoft & Amazon Türk çalışanları, TACAWA derneği)",
        "pros": "Amazon ve Microsoft ana üssü, eyalet gelir vergisi sıfır, doğa harikası (dağlar, göller).",
        "cons": "Uzun ve gri/yağmurlu kışlar (D vitamini eksikliği riski), pahalı gayrimenkul.",
    },
    "north_carolina": {
        "title": "North Carolina (Raleigh, Durham, Charlotte)",
        "income_tax": "%4.5 (Sabit düşük vergi)",
        "sales_tax": "%4.75 - %7.5",
        "rent_1br": "$1,250 - $1,550",
        "tech_salary": "$110,000 - $145,000",
        "nurse_salary": "$75,000 - $95,000",
        "climate": "4 mevsim dengeli; ılıman kışlar, sıcak yazlar",
        "car": "Zorunlu 🚗",
        "turkish_community": "Orta ölçekli (Research Triangle Türk akademisyenleri ve Aziz Sancar Vakfı)",
        "pros": "Aileler için mükemmel; uygun konut, harika okullar, Research Triangle Park (biyoteknoloji & yazılım).",
        "cons": "Büyük metropol heyecanı arayanlara göre sakin kalabilir, araçsız yaşamak imkansız.",
    },
    "new_york": {
        "title": "New York (NYC - Manhattan, Brooklyn, Queens)",
        "income_tax": "%4 - %10.9 (Eyalet + Şehir vergisi)",
        "sales_tax": "%8.875",
        "rent_1br": "$2,500 - $3,500+",
        "tech_salary": "$140,000 - $200,000+",
        "nurse_salary": "$95,000 - $130,000",
        "climate": "Karasal; soğuk ve karlı kışlar, sıcak/nemli yazlar",
        "car": "Gereksiz 🚇 (24 saat çalışan metro ve toplu taşıma)",
        "turkish_community": "ABD'nin en köklü Türk topluluğu (Paterson NJ / Brooklyn, THY ve AJet seferleri)",
        "pros": "Dünya finans/sanat başkenti, araç gerektirmeyen yaşam, sınırsız sosyal ve iş ağı.",
        "cons": "Aşırı yüksek yaşam maliyeti ve çifte vergilendirme (State + NYC City Tax), küçük yaşam alanları.",
    },
}


def get_state_keys() -> List[str]:
    return list(STATE_DETAILS.keys())


def get_state_profile(key: str) -> Optional[Dict[str, Any]]:
    clean = key.lower().strip().replace(" ", "_")
    return STATE_DETAILS.get(clean)


def compare_states(state1_key: str, state2_key: str) -> str:
    """Generate side-by-side comparison of two US states."""
    s1 = get_state_profile(state1_key)
    s2 = get_state_profile(state2_key)
    if not s1 or not s2:
        return "Lütfen geçerli iki eyalet adı giriniz (Örn: `texas`, `california`, `florida`, `washington`, `north_carolina`, `new_york`)."

    lines = [
        f"🏙️ *Eyalet Kıyaslama: {s1['title']} vs {s2['title']}*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏛️ *Eyalet Gelir Vergisi:*",
        f"• {s1['title'].split('(')[0]}: *{s1['income_tax']}*",
        f"• {s2['title'].split('(')[0]}: *{s2['income_tax']}*",
        "",
        f"🏠 *Ortalama 1+1 Kira:*",
        f"• {s1['title'].split('(')[0]}: *{s1['rent_1br']}*",
        f"• {s2['title'].split('(')[0]}: *{s2['rent_1br']}*",
        "",
        f"💻 *Yazılım / Tech Medyan Maaş:*",
        f"• {s1['title'].split('(')[0]}: *{s1['tech_salary']}*",
        f"• {s2['title'].split('(')[0]}: *{s2['tech_salary']}*",
        "",
        f"🩺 *Hemşirelik / Sağlık Maaşı:*",
        f"• {s1['title'].split('(')[0]}: *{s1['nurse_salary']}*",
        f"• {s2['title'].split('(')[0]}: *{s2['nurse_salary']}*",
        "",
        f"🚗 *Araç İhtiyacı & Ulaşım:*",
        f"• {s1['title'].split('(')[0]}: {s1['car']}",
        f"• {s2['title'].split('(')[0]}: {s2['car']}",
        "",
        f"🇹🇷 *Türk Topluluğu & Uçuşlar:*",
        f"• {s1['title'].split('(')[0]}: {s1['turkish_community']}",
        f"• {s2['title'].split('(')[0]}: {s2['turkish_community']}",
        "",
        f"⚖️ *Stratejik Karşılaştırma:*",
        f"• *{s1['title'].split('(')[0]} Artısı:* {s1['pros']}",
        f"• *{s2['title'].split('(')[0]} Artısı:* {s2['pros']}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Koçun Tavsiyesi:* Eğer bütçeniz $25K altındaysa veya sıfır eyalet vergisiyle hızla birikim yapmak istiyorsanız Texas veya Florida; bütçeniz genişse ve teknoloji ağının merkezinde olmak istiyorsanız California veya Washington idealdir.",
    ]
    return "\n".join(lines)


# ============================================================================
# 3. CASE NUMBER & VİZE BÜLTENİ ANALİZÖRÜ (CASE NUMBER & VISA BULLETIN)
# ============================================================================

def _build_case_kcc_email_draft(
    case_no: str,
    rank: int,
    tier_code: str,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Build a proactive, ready-to-send KCC/Embassy email tailored to the rank and user profile."""
    ds260 = (profile or {}).get("ds260", {}) if profile else {}
    full_name = (ds260.get("full_name") or "").strip() or "[AD SOYAD - PASAPORTTAKİ GİBİ]"
    birth_info = (ds260.get("birth_info") or "").strip() or "[DOĞUM TARİHİ: YYYY-MM-DD]"

    if tier_code in ("high", "very_high"):
        pitch = (
            f"Sıra numaran (*#{rank:,}*) yüksek dilimde olduğu ve 30 Eylül mali yıl sonu kesin yasal sınır olduğu için "
            "pasif beklemek büyük risk taşır. Numaran Vize Bülteni'nde (Visa Bulletin) 'Current' olduğu sabah tek bir gün "
            "bile kaybetmeden mülakat mektubunun (2NL) atanabilmesi için KCC'deki DS-260 dosyanın *'Documentarily Qualified / Processed'* "
            "(işlenmiş ve mülakata hazır) statüsünde beklediğinden emin olmalıyız. Hemen aksiyon alabilmemiz için "
            "*KCC'ye (`KCCDV@state.gov`) mail atabiliriz, onlara şu şekilde söyleyelim:*"
        )
        subject = f"Urgent Case Status & DS-260 Readiness Inquiry - {case_no} - {full_name}"
        body = (
            "Dear Kentucky Consular Center,\n\n"
            "I am a Diversity Visa selectee writing to kindly confirm the processing status and interview readiness of my immigrant visa case.\n\n"
            f"Case Number: {case_no}\n"
            f"Principal Applicant Name: {full_name}\n"
            f"Date / Place of Birth: {birth_info}\n\n"
            "Given our case rank and the strict September 30 fiscal year deadline, I want to ensure that our submitted DS-260 Immigrant Visa Electronic Application has been fully processed and that there are no pending administrative holds or missing details preventing immediate interview scheduling at the U.S. Embassy as soon as our case number becomes current in the Visa Bulletin.\n\n"
            "Please let me know if our case is currently marked as ready for scheduling once current, or if any further action is required on my part.\n\n"
            "Thank you very much for your time and assistance.\n\n"
            "Sincerely,\n"
            f"{full_name}"
        )
    else:
        pitch = (
            f"Sıra numaran (*#{rank:,}*) avantajlı bir pencerede yer alıyor; ancak DS-260 formun KCC tarafından "
            "incelenip 'mülakata hazır' (processed) olarak işaretlenmezse, numaran 'Current' olsa bile randevu mektubun (2NL) "
            "aylarca gecikebilir. Süreci şansa bırakmamak için *KCC'ye (`KCCDV@state.gov`) dosya hazırlık teyit maili atabiliriz, "
            "onlara şu şekilde söyleyelim:*"
        )
        subject = f"Case Status & DS-260 Processing Confirmation - {case_no} - {full_name}"
        body = (
            "Dear Kentucky Consular Center,\n\n"
            "I am writing to respectfully inquire about the processing status of my submitted DS-260 Immigrant Visa Electronic Application.\n\n"
            f"Case Number: {case_no}\n"
            f"Principal Applicant Name: {full_name}\n"
            f"Date / Place of Birth: {birth_info}\n\n"
            "Could you please confirm whether my DS-260 form has been reviewed and processed, and whether my case is completely ready for interview scheduling when our rank is reached?\n\n"
            "Thank you very much for your assistance.\n\n"
            "Sincerely,\n"
            f"{full_name}"
        )

    return {
        "to": "KCCDV@state.gov",
        "subject": subject,
        "pitch": pitch,
        "body": body,
    }


def analyze_case_number(raw_case: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Parse and analyze Green Card Diversity Visa Case Number (e.g. 2027EU00014520 or EU28500)."""
    clean = re.sub(r"[\s\-_]+", "", (raw_case or "").upper())
    match = re.match(r"^(202[5-8])([A-Z]{2})0*([1-9]\d*)$", clean)
    if not match:
        short_match = re.match(r"^(EU|AS|AF|OC|SA)0*([1-9]\d*)$", clean)
        if short_match:
            region_code, rank_str = short_match.groups()
            year = "2027"
            clean = f"{year}{region_code}{int(rank_str):08d}"
        else:
            return {
                "valid": False,
                "raw": raw_case,
                "message": "Geçerli bir Case Number formatı girilmedi (Örn: `2027EU00014250`, `2027AS1200` veya `EU28500`).",
            }
    else:
        year, region_code, rank_str = match.groups()

    rank = int(rank_str)

    regions = {
        "EU": ("Avrupa (Europe - Türkiye bu bölgededir)", 35000),
        "AS": ("Asya (Asia)", 22000),
        "AF": ("Afrika (Africa)", 65000),
        "OC": ("Okyanusya (Oceania)", 2500),
        "SA": ("Güney Amerika / Karayipler", 3000),
    }

    reg_name, typical_cutoff = regions.get(region_code, (region_code, 30000))

    # Derecelendirme (Rank Tier) ve Proaktif Senaryolar
    if rank <= 9000:
        tier_code = "low"
        tier = "Düşük Numara (Altın Sıra) 🌟"
        period = "Ekim - Ocak (İlk Mülakat Dalgası)"
        risk = "Çok Düşük. DS-260 formunuz onaylandıktan sonra mali yılın başında mülakata çağrılma olasılığınız çok yüksektir."
        scenarios = [
            "🟢 *Senaryo 1 (İdeal Akış - %75):* DS-260 formunu erken gönderdiğinde KCC incelemesi hızla biter ve Ekim-Ocak arasındaki ilk bültenlerde Ankara mülakatın (2NL) atanır.",
            "🟡 *Senaryo 2 (DS-260 Gecikmesi / Dar Takvim - %20):* Mahkeme/kayıt takvimi sıkışırsa veya DS-260 geç gönderilirse ilk dalga kaçırılır ve mülakat İlkbahara kayar.",
            "🔵 *Senaryo 3 (İdari İşlem / 221g Koruması - %5):* Erken mülakata girdiğin için teknik/güvenlik soruşturması (221g) verilse bile 30 Eylül sınırına kadar bolca vaktin kalır.",
        ]
        immediate_actions = [
            "DS-260 formunu eksiksiz doldurup hemen gönder ('3 Göz Kuralı' denetimini `/ds260` ile çalıştır).",
            "Gönderimden 3-4 hafta sonra KCC'ye aşağıdaki hazır maili atarak dosyanın 'Processed' olduğunu teyit et.",
            "Unganlar sağlık muayenesi için aşı kartı / antikor testlerini ve Formül A/B belgelerini şimdiden tamamla.",
        ]
    elif rank <= 22000:
        tier_code = "medium"
        tier = "Orta Numara (Güvenli Alan) 🟢"
        period = "Şubat - Nisan (Bahar Dönemi)"
        risk = "Düşük/Normal. Vize bülteninde sıra düzenli ilerler; DS-260'ı geciktirmeden göndermek ve KCC onayını takip etmek kritiktir."
        scenarios = [
            "🟢 *Senaryo 1 (Normal Bülten İlerlemesi - %65):* Vize bülteni kış aylarında düzenli yükselir, Şubat-Nisan döneminde numaran 'Current' olur ve Ankara'dan randevu gelir.",
            "🟡 *Senaryo 2 (Ankara Konsolosluğu Yığılması - %25):* Numaran Baharda Current olsa bile Ankara'daki mülakat kuyruğu nedeniyle 2NL mektubun Mayıs-Haziran'a sarkabilir.",
            "🔴 *Senaryo 3 (Daraltılmış Takvim Sıkışması - %10):* DV-2027 takvimi mahkeme nedeniyle geç başlarsa tüm orta numaralar yaz aylarına sıkışır; KCC'de dosyası hazır olmayanlar sıra kaybeder.",
        ]
        immediate_actions = [
            "DS-260 formunu bekletmeden CEAC üzerinden tamamla; KCC kuyruğunda ön sıraya geç.",
            "KCC'ye (`KCCDV@state.gov`) dosya işleme teyit maili atarak 'Current' olduğun gün 2NL almaya hazır ol.",
            "Eğer mülakatta 221(g) (idari işlem) riski taşıyan teknik/yazılım mesleğin varsa İngilizce detaylı CV'ni şimdiden hazırla.",
        ]
    elif rank <= 34000:
        tier_code = "high"
        tier = "Yüksek Numara (Kritik Takip & Proaktif Aksiyon) 🟡"
        period = "Mayıs - Temmuz (Yaz Dönemi / Kritik Pencere)"
        risk = "Orta-Yüksek. Numaranızın 'Current' olması yaz aylarını bulabilir. Ankara Konsolosluğu'ndaki dosya yoğunluğu ve 30 Eylül mali yıl sınırına karşı proaktif KCC takibi ve B planı şarttır."
        scenarios = [
            "🟢 *Senaryo 1 (Erken DS-260 + KCC Teyidi ile Yaz Mülakatı - %50):* DS-260 formun önceden işlenmiş ('Processed') beklediği için Mayıs-Temmuz bülteninde Current olduğun anda ilk boş slottan 2NL alırsın.",
            "🟡 *Senaryo 2 (Ankara Randevu Darboğazı & Dosya Taşıma İhtiyacı - %35):* Numaran Current olur ancak Ankara'da yaz kotaları dolarsa, yasal oturum/çalışma/öğrenci iznin olan alternatif bir konsolosluğa dosya transferi (Case Transfer) hayat kurtarır.",
            "🔴 *Senaryo 3 (30 Eylül Mali Yıl Kapanış Riski - %15):* Mülakat Ağustos-Eylül'e kalırsa tek bir eksik evrak veya 221(g) idari işlemi vize hakkını 30 Eylül'de yakabilir; sıfır hata ile mülakata girilmelidir.",
        ]
        immediate_actions = [
            "🚨 *1. Adım (Hemen):* DS-260 formunu tek bir gün geciktirmeden gönder; yüksek numaralarda KCC onay tarihi (DQ) kimlerin önce çağrılacağını belirler!",
            "📧 *2. Adım (KCC İletişimi):* Aşağıda senin için hazırladığım İngilizce maili `KCCDV@state.gov` adresine göndererek dosyanın mülakat atamasına %100 hazır olduğunu yazılı teyit ettir.",
            "✈️ *3. Adım (Konsolosluk B Planı):* Yurt dışında yasal oturum, öğrenci (F-1/Erasmus/Yüksek Lisans) veya çalışma izni imkanın varsa Ankara kuyruğuna takılmamak için `/dosya_tasima` stratejisini hazır tut.",
            "🩺 *4. Adım (Sıfır 221g Riski):* Yaz mülakatlarında idari işlem (221g) bekleyecek vakit yoktur; tüm e-Devlet evraklarını, aşıları ve Public Charge banka dökümünü eksiksiz hazırla.",
        ]
    else:
        tier_code = "very_high"
        tier = "Çok Yüksek Numara (Mali Yıl Kapanış & Acil Müdahale) 🔴"
        period = "Ağustos - Eylül (Son Çağrılar / All-Current Dönemi)"
        risk = "Yüksek. 30 Eylül mali yıl sonu kesin yasal sınırdır (bu tarihten sonra tek bir vize bile basılamaz). DS-260'ı ilk gün göndermek, KCC ile aktif yazışmak ve gerekirse dosya transferi / acil randevu talep etmek zorunludur."
        scenarios = [
            "🟢 *Senaryo 1 (Yaz Sonu 'Current' + Hazır Dosya ile Son Dakika Golü - %40):* DS-260 formun aylar öncesinden KCC'de onaylanmış beklediği için Ağustos/Eylül bülteninde bölge 'Current' olduğu an randevun atanır ve Eylül bitmeden vizen basılır.",
            "🟡 *Senaryo 2 (Dosya Transferi veya Konsolosluk Acil Randevu Müdahalesi - %35):* Ankara'da Eylül slotları dolarsa, oturum izni olan başka bir konsolosluğa transfer veya Current olunduğunda doğrudan Konsolosluğa 'Mali Yıl Sonu Acil Randevu' (Expedited Scheduling) maili atarak slot alınır.",
            "🔴 *Senaryo 3 (Kota Dolumu veya 30 Eylül Süre Aşımı - %25):* Yıllık 55.000 vize kotası Eylül'den önce biterse veya mülakat sonrası 221(g) idari işlemi 30 Eylül'ü aşarsa vize hakkı düşer; bu yüzden EB-2 NIW / E-2 / F-1 gibi B planları paralel yürütülmelidir.",
        ]
        immediate_actions = [
            "🚨 *1. Adım (Kritik Öncelik):* DS-260 formunu derhal gönder; çok yüksek numaralarda DS-260'ı geç gönderenlerin dosyası 30 Eylül'e kadar KCC'den bile çıkamaz!",
            "📧 *2. Adım (KCC Durum & Hazırlık Maili):* Aşağıdaki hazır İngilizce maili `KCCDV@state.gov` adresine göndererek DS-260 incelemesinin tamamlandığını ('Documentarily Qualified') mutlaka teyit et.",
            "🏛️ *3. Adım (Konsolosluk Acil Slot & Transfer):* Numaran bültende Current olur olmaz 2NL gelmezse beklemeyip doğrudan konsolosluğa *Mali Yıl Sonu Acil Randevu* maili atacağız (aşağıdaki butondan taslağı alabilirsin).",
            "🛡️ *4. Adım (Paralel B Planı):* Çok yüksek numarada riski sıfırlamak için `/vize_analiz` üzerinden EB-2 NIW, F-1 STEM OPT veya E-2 B planımızı hemen devreye sok.",
        ]

    # Kullanıcı profilindeki eksiklere göre kişiselleştirilmiş ek aksiyon uyarısı
    if profile:
        ds260 = profile.get("ds260", {})
        filled_ds = sum(1 for v in ds260.values() if v and str(v).strip())
        if filled_ds < 5:
            immediate_actions.insert(
                0,
                f"⚠️ *Profil Tespiti:* `/ds260` simülatöründe henüz {filled_ds}/10 alan dolu. KCC'de sıra kaybetmemek için önce adres ve 10 yıllık iş geçmişini hemen tamamlayalım.",
            )

    kcc_email = _build_case_kcc_email_draft(clean, rank, tier_code, profile)

    return {
        "valid": True,
        "raw": clean,
        "year": year,
        "region_code": region_code,
        "region_name": reg_name,
        "rank": rank,
        "typical_cutoff": typical_cutoff,
        "tier_code": tier_code,
        "tier": tier,
        "projected_period": period,
        "risk_analysis": risk,
        "scenarios": scenarios,
        "immediate_actions": immediate_actions,
        "kcc_email": kcc_email,
    }


def format_case_analysis(analysis: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> str:
    if not analysis.get("valid"):
        return f"⚠️ {analysis.get('message', 'Geçersiz format.')}"

    kcc_email = analysis.get("kcc_email") or _build_case_kcc_email_draft(
        analysis["raw"],
        analysis["rank"],
        analysis.get("tier_code", "medium"),
        profile,
    )
    scenarios = analysis.get("scenarios", [])
    immediate_actions = analysis.get("immediate_actions", [])

    lines = [
        f"🔢 *DV-{analysis['year']} Case Number Proaktif Strateji & Eylem Planı*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📋 *Numaranız:* `{analysis['raw']}`",
        f"🌍 *Bölge:* {analysis['region_name']}",
        f"🎯 *Sıra Numaranız:* *#{analysis['rank']:,}*",
        f"🏷️ *Sıra Grubu:* *{analysis['tier']}*",
        f"📅 *Tahmini Mülakat Penceresi:* *{analysis['projected_period']}*",
        "",
        f"⚖️ *Stratejik Risk & Süreç Değerlendirmesi:*",
        f"{analysis['risk_analysis']}",
    ]

    if scenarios:
        lines.extend([
            "",
            "🔮 *SENİN YERİNE DÜŞÜNDÜM: OLASI SENARYOLAR*",
            *scenarios,
        ])

    if immediate_actions:
        lines.extend([
            "",
            "⚡ *ZAMAN KAYBETMEMEK İÇİN HEMEN ALACAĞIMIZ AKSİYONLAR*",
        ])
        for idx, act in enumerate(immediate_actions, 1):
            lines.append(f"{idx}. {act}" if not act.startswith(("🚨", "📧", "✈️", "🩺", "🏛️", "🛡️", "⚠️")) else f"• {act}")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🧠 *PROAKTİF KCC HAMLEMİZ (\"ONLARA ŞU ŞEKİLDE SÖYLEYELİM\"):*",
        kcc_email["pitch"],
        "",
        f"• *Alıcı:* `{kcc_email['to']}`",
        f"• *Subject:* `{kcc_email['subject']}`",
        "```text",
        kcc_email["body"],
        "```",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "👇 *Aşağıdaki butonlardan durumuna göre diğer hazır resmi mailleri (Acil Mülakat, Dosya Taşıma, DS-260 Unlock, 221g Takip) tek tıkla üretebilirsin:*",
    ])
    return "\n".join(lines)


# ============================================================================
# 4. 360° GREEN CARD & DS-260 HAZIRLIK VE RİSK KARNESİ (READINESS AUDIT)
# ============================================================================

def generate_readiness_audit(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Audit user profile and compute an objective Readiness Score (0-100)."""
    chk = profile.get("checklist", {})
    ds260 = profile.get("ds260", {})
    facts = profile.get("user_facts", {})

    score = 0
    pillars: List[Tuple[str, int, int, str]] = []  # (Name, earned, total, status)
    red_flags: List[str] = []
    priorities: List[str] = []

    # Pillar 1: Pasaport & Kimlik (20 Puan)
    p1 = 0
    if chk.get("passport_valid"):
        p1 += 10
    else:
        red_flags.append("Süresi geçerli pasaport kontrolü tamamlanmamış.")
        priorities.append("Pasaportunuzun geçerlilik süresini (en az 2028'e kadar) kontrol edin.")
    if chk.get("passport_scan"):
        p1 += 10
    else:
        priorities.append("Pasaport kimlik sayfasını JPEG olarak taratın.")
    pillars.append(("🛂 Pasaport & Kimlik Altyapısı", p1, 20, "Hazır" if p1 == 20 else "Eksik"))
    score += p1

    # Pillar 2: Biyometrik Fotoğraf (20 Puan)
    p2 = 0
    if chk.get("photo_taken"):
        p2 += 10
    if chk.get("photo_tested"):
        p2 += 10
    if p2 < 20:
        red_flags.append("Biyometrik fotoğraf henüz botta veya resmi araçta test edilmedi.")
        priorities.append("Son 6 ayda çekilmiş 600x600 px fotoğrafınızı botta `/fotograf` ile test edin.")
    pillars.append(("📸 Biyometrik Fotoğraf Standartları", p2, 20, "Onaylandı" if p2 == 20 else "Test Edilmedi"))
    score += p2

    # Pillar 3: DS-260 Veri Hazırlığı (25 Puan)
    filled_ds = sum(1 for v in ds260.values() if v and v.strip())
    total_ds = max(1, len(ds260))
    p3 = int((filled_ds / total_ds) * 25)
    if filled_ds < 5:
        red_flags.append("DS-260 simülatöründe geçmiş adres ve iş kayıtları eksik.")
        priorities.append("16 yaşından itibaren adreslerinizi ve 10 yıllık SGK geçmişinizi `/ds260`'a kaydedin.")
    pillars.append(("📝 DS-260 & e-Devlet Evrak Altyapısı", p3, 25, f"{filled_ds}/{total_ds} Alan Dolu"))
    score += p3

    # Pillar 4: Finansal Güvence / Public Charge (15 Puan)
    p4 = 0
    budget_raw = facts.get("butce", "")
    budget_val = parse_numeric_budget(budget_raw)
    if budget_val >= 20000:
        p4 = 15
    elif budget_val >= 10000:
        p4 = 10
    elif budget_raw:
        p4 = 5
        red_flags.append("Bütçeniz tek başına kamu yükü (Public Charge) şüphesini kaldırmak için sınırda.")
    else:
        p4 = 5
        priorities.append("Taşınma bütçenizi `/profil butce <miktar>` ile kaydederek runway hesabı yapın.")
    pillars.append(("💵 Finansal Birikim & Public Charge", p4, 15, f"${budget_val:,.0f}" if budget_val else "Belirtilmedi"))
    score += p4

    # Pillar 5: Sağlık & Aşı Muayenesi (10 Puan)
    p5 = 10 if chk.get("vaccine_check") else 0
    if p5 == 0:
        priorities.append("Eksik aşılarınızı (Tetanoz, MMR, Hepatit B) aile hekiminizde tamamlayın.")
    pillars.append(("🩺 Sağlık & Aşı Uygunluğu", p5, 10, "Tamam" if p5 == 10 else "Eksik"))
    score += p5

    # Pillar 6: Konsolosluk Mülakat Simülasyonu (10 Puan)
    p6 = 10 if chk.get("mock_interview") else 0
    if p6 == 0:
        priorities.append("Botta `/mulakat` komutuyla 6 soruluk vize provasını tamamlayın.")
    pillars.append(("🎯 Mülakat Provasi & Özgüven", p6, 10, "Tamamlandı" if p6 == 10 else "Yapılmadı"))
    score += p6

    # Derecelendirme Rozeti
    if score >= 85:
        badge = "🏆 Şampiyonlar Ligi (Kusursuza Yakın)"
        status_color = "🟢"
    elif score >= 60:
        badge = "⚡ Güçlü İlerleme (Birkaç Kritik Eksiği Var)"
        status_color = "🟡"
    else:
        badge = "⚠️ Başlangıç Aşaması (Hızlanmak Şart)"
        status_color = "🔴"

    return {
        "score": score,
        "badge": badge,
        "status_color": status_color,
        "pillars": pillars,
        "red_flags": red_flags,
        "priorities": priorities[:3],
    }


def format_audit_report(audit: Dict[str, Any]) -> str:
    lines = [
        f"📊 *360° Green Card Hazırlık ve DS-260 Risk Karnesi*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Genel Hazırlık Puanı: *{audit['score']} / 100* {audit['status_color']}",
        f"Durum Rozeti: *{audit['badge']}*",
        "",
        "📋 *ALAN BAZINDA DERECELENDİRME:*",
    ]
    for name, earned, total, status in audit["pillars"]:
        bar = "█" * (earned // 2) + "░" * ((total - earned) // 2)
        lines.append(f"• {name}: *{earned}/{total}* ({status})\n  `[{bar}]`")

    if audit["red_flags"]:
        lines.extend(["", "⚠️ *DİKKAT EDİLMESİ GEREKEN RİSKLER:*"])
        for rf in audit["red_flags"]:
            lines.append(f"• {rf}")

    if audit["priorities"]:
        lines.extend(["", "🎯 *SIRADAKİ EN ACİL 3 EYLEM ADIMI:*"])
        for i, pri in enumerate(audit["priorities"], 1):
            lines.append(f"{i}. {pri}")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Nasıl Puan Yükseltilir?* Eksik adımları tamamladıkça `/checklist` ve `/ds260` üzerinden işaretleyin, karneniz anında güncellensin!",
    ])
    return "\n".join(lines)


# ============================================================================
# 5. ALTERNATİF VİZE ROTALARI & B PLANI REHBERİ (ALTERNATIVE VISA ROUTES)
# ============================================================================

def get_visa_routes_guide(profile: Optional[Dict[str, Any]] = None) -> str:
    """Provide tailored overview of alternative US visa routes based on profile."""
    facts = profile.get("user_facts", {}) if profile else {}
    job = facts.get("meslek", "").lower()
    edu = facts.get("egitim", "").lower()

    tailored_intro = ""
    if "yazılım" in job or "mühendis" in job or "veri" in job or "doktora" in edu or "yüksek lisans" in edu:
        tailored_intro = (
            "💡 *Sana Özel Stratejik Tavsiye:* Eğitim ve meslek profilin (Mühendislik / İleri Derece), "
            "şirket sponsorluğu gerektirmeyen **EB-2 NIW (National Interest Waiver)** doğrudan Green Card rotası "
            "veya **O-1A** vizesi için son derece uygundur. Çekilişi beklerken bu rotayı eşzamanlı başlatabilirsin!\n\n"
        )

    lines = [
        "🇺🇸 *Green Card Dışındaki Alternatif ABD Çalışma & Göçmenlik Rotaları*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        tailored_intro,
        "1️⃣ *EB-2 NIW (National Interest Waiver) — En Güçlü B Planı:*",
        "• *Nedir?* Şirket teklifi veya sponsor OLMADAN, kendi adınıza doğrudan Green Card başvurusu yapabilirsiniz.",
        "• *Kimler İçin?* Lisans + 5 yıl deneyim veya Yüksek Lisans/Doktora sahibi mühendisler, araştırmacılar, sağlıkçılar.",
        "• *Avantajı:* Çekiliş şansına bağlı değildir; liyakatinizle onay alırsınız.",
        "",
        "2️⃣ *O-1 (Olağanüstü Yetenek Vizesi):*",
        "• *Nedir?* Alanında ulusal veya uluslararası başarı göstermiş kişilere sınırsız süreyle verilen çalışma vizesi.",
        "• *Kriterler:* Patentler, bilimsel makaleler, sektörde basında yer alma, yüksek maaş veya jüri üyeliği.",
        "",
        "3️⃣ *H-1B (Uzman Çalışan Vizesi):*",
        "• *Nedir?* Bir ABD şirketinin sizin adınıza sponsor olduğu en yaygın çalışma vizesi.",
        "• *Önemli Detay:* Yıllık kura sistemi vardır (%20-25 çıkma şansı). Ancak üniversiteler ve kar amacı gütmeyen araştırma kurumları kura şartından muaftır (Cap-Exempt).",
        "",
        "4️⃣ *L-1 (Şirket İçi Transfer Vizesi):*",
        "• *Nedir?* Türkiye'de uluslararası bir şirkette en az 1 yıl kesintisiz çalıştıktan sonra şirketin ABD ofisine yönetici (L-1A) veya uzman (L-1B) olarak transfer olmak.",
        "• *Büyük Avantajı:* Kura yoktur, eşiniz de ABD'de tam çalışma iznine (L-2S) sahip olur.",
        "",
        "5️⃣ *F-1 STEM OPT (Öğrenci Yüksek Lisans Rotası):*",
        "• *Nedir?* ABD'de STEM (Mühendislik, Veri, IT vb.) alanında 1-2 yıllık master programı tamamlamak.",
        "• *Avantajı:* Mezuniyet sonrası 3 yıl kesintisiz yasal çalışma hakkı (STEM OPT) verir; bu sürede H-1B veya Green Card'a geçiş yapılır.",
        "",
        "6️⃣ *E-2 (Yatırımcı Vizesi):*",
        "• *Nedir?* Türkiye ile ABD arasındaki ticaret anlaşması sayesinde ortalama $75K-$100K+ sermaye ile aktif bir işletme kurarak ailecek ABD'de yaşama hakkı.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💬 *Danışman Notu:* 'Yalnızca Green Card çekilişine bel bağlamak kumardır; B ve C planlarını paralel yürütmek ise vizyondur.' Bu rotaların herhangi biri hakkında detaylı soru sormak istersen doğrudan mesaja yazabilirsin!",
    ]
    return "\n".join(lines)


# ============================================================================
# 6. GREEN CARD & GÖÇMENLİK SÖZLÜĞÜ (IMMIGRATION GLOSSARY)
# ============================================================================

GLOSSARY_TERMS: Dict[str, str] = {
    "ceac": "*CEAC (Consular Electronic Application Center):* Dışişleri Bakanlığı'nın resmi göçmenlik portalıdır. DS-260 formunun doldurulduğu ve dosya durumunun (Ready, Issued, Refused) sorgulandığı yerdir (ceac.state.gov).",
    "2nl": "*2NL (Second Notification Letter):* KCC tarafından gönderilen 'İkinci Bildirim Mektubu'dur. Numaranız vize bülteninde 'Current' olduğunda ve Ankara Konsolosluğu mülakat randevu tarihinizi belirlediğinde CEAC'a yüklenir.",
    "221g": "*221(g) İdari İşlem (Administrative Processing):* Mülakat sonrası memurun ek evrak talep etmesi veya adayın geçmişini (özellikle teknoloji/savunma alanlarındaki kişileri) detaylı güvenlik incelemesine alması durumudur. Genellikle 2-8 hafta sürer.",
    "kcc": "*KCC (Kentucky Consular Center):* Diversity Visa (Green Card) çekilişini yöneten, DS-260 formlarını ve ilk belgeleri inceleyip konsolosluklara sevk eden merkezi Dışişleri Bakanlığı birimidir.",
    "public charge": "*Public Charge (Kamu Yükü):* ABD Göçmenlik Kanunu Bölüm 212(a)(4) uyarınca, adayın ABD'ye gittiğinde devlet yardımına muhtaç hale gelmeyeceğini (yeterli birikim, meslek, İngilizce veya Form I-134 sponsoru ile) kanıtlama zorunluluğudur.",
    "form i-134": "*Form I-134 (Affidavit of Support):* ABD'de yaşayan bir ABD vatandaşı veya Green Card sahibinin, 'Bu kişi ABD'ye geldiğinde gerekirse geçimini ben üstleneceğim' diyerek sizin adınıza konsolosluğa sunduğu resmi garanti belgesidir.",
    "ds-260": "*DS-260 Göçmen Vize Başvuru Formu:* Çekilişi kazandıktan sonra internet üzerinden doldurulan, 16 yaşından itibaren tüm adres, iş, okul, aile ve güvenlik geçmişinizi içeren kapsamlı elektronik başvuru formudur.",
    "ds-5501": "*DS-5501:* Her yıl Ekim-Kasım aylarında dvprogram.state.gov üzerinden doldurulan ilk çekiliş başvuru formunun teknik adıdır.",
    "uscis fee": "*USCIS Immigrant Fee ($220):* Vizeniz konsoloslukta basıldıktan sonra, fiziksel Green Card kartınızın üretilip ABD adresinize postalanması için USCIS'e online ödenen resmi harçtır.",
    "port of entry": "*Port of Entry (POE):* ABD'ye vizenizle ilk ayak bastığınız uluslararası havalimanıdır (ör. JFK, Houston IAH, LAX). Pasaport kontrol memuru burada göçmenlik paketinizi açar ve sizi yasal Green Card sahibi (LPR) yapar.",
    "cutoff": "*Cut-off Numarası:* Her ay Visa Bulletin'de ilan edilen tavan sıra numarasıdır. Numaranız bu sınırın altındaysa dosyanız 'Current' (aktif) hale gelir ve mülakat sıranız açılır.",
    "cross-chargeability": "*Cross-Chargeability (Çapraz Ülke Kotası):* Eşinizin doğduğu ülkenin Green Card kotası sizin doğduğunuz ülkeden daha avantajlıysa, eşinizin doğum yeri kotası üzerinden değerlendirilme hakkınızdır.",
}


def lookup_glossary(query: str) -> str:
    """Lookup an immigration term or show all available terms."""
    q = (query or "").strip().lower()
    if not q:
        lines = [
            "📖 *Green Card & ABD Göçmenlik Sözlüğü*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "Aramak istediğiniz terimi `/sozluk <terim>` şeklinde yazabilirsiniz.\n",
            "Mevcut terimler:\n"
            + " • ".join([f"`{k.upper()}`" for k in GLOSSARY_TERMS.keys()]),
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "Örnek: `/sozluk 2NL` veya `/sozluk Public Charge`",
        ]
        return "\n".join(lines)

    for k, v in GLOSSARY_TERMS.items():
        if k in q or q in k:
            return f"📖 {v}"

    return (
        f"🔍 `{query}` terimi sözlükte doğrudan bulunamadı.\n\n"
        "Bunu doğrudan bir soru olarak bana sorabilirsiniz: "
        f"_'{query} nedir, süreçte ne anlama gelir?'_"
    )


# ============================================================================
# 7. MAHKEME & TAKVİM STRATEJİSTİ (COURT & TIMELINE PROACTIVE ORACLE)
# ============================================================================

def analyze_court_and_timeline(facts: Optional[Dict[str, str]] = None) -> str:
    """Proactive legal analysis of DV-2027 court battles, Ninth Circuit appeal, and strategic timeline."""
    facts = facts or {}
    job = facts.get("meslek", "")
    target = facts.get("hedef_lokasyon", "")

    tailored = ""
    if job or target:
        tailored = f"\n👤 *Sana Özel Stratejik Tavsiye ({job or 'Danışan'}{' - ' + target if target else ''}):*\nMahkeme takvimi ertelenirken zaman kaybetme; mülakat ve iş hazırlıklarını tamamla.\n"

    lines = [
        "⚖️ *DV-2027 Mahkeme Durumu, Temyiz Kararı & Stratejik Takvim Analizi*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🏛️ *DAVA DOSYASI:* _Red Eagle Law, LC v. Marco Rubio / U.S. Department of State_",
        "",
        "📌 *ŞU ANDA HUKUKEN NE OLDU?*",
        "1️⃣ *Bölge Mahkemesi Kararı (District Court):* Federal yargıç, Dışişleri Bakanlığı'nın DV-2027'yi erteleme kararını hukuka aykırı bularak kayıt portalının açılması yönünde tedbir (preliminary injunction) vermişti.",
        "2️⃣ *Temyiz Mahkemesi Kararı (Ninth Circuit Court of Appeals):* Hükümetin itirazı üzerine 9. Temyiz Mahkemesi, esastan inceleme tamamlanana kadar alt mahkemenin kararını *GEÇİCİ OLARAK DURDURDU (Stay of Order)*.",
        "3️⃣ *Fiili Sonuç:* Portalı açma zorunluluğu şu an askıda. Ancak dava esastan devam ediyor ve yeni duruşma/karar bekleniyor.",
        "",
        "🔮 *SENİN YERİNE DÜŞÜNÜYORUM: ÖNÜMÜZDEKİ 3 OLASI SENARYO*",
        "",
        "🟢 *Senaryo A: Hızlı Temyiz Kararı veya Hükümet Uzlaşması (%40 İhtimal)*",
        "• Mahkeme alt mahkemeyi haklı bulursa veya Dışişleri Bakanlığı 1$ ödeme altyapısını tamamlayıp itirazını çekerse;",
        "• *Takvim:* Başvuru sistemi 30 günlük sıkıştırılmış bir periyotla açılır. Sonuçlar yine Mayıs 2027 civarında açıklanır ve mülakatlar zamanında tamamlanır.",
        "",
        "🟡 *Senaryo B: Bahar Kayması & Daraltılmış Mülakat Penceresi (%35 İhtimal)*",
        "• Kararın gecikmesi durumunda Dışişleri Bakanlığı başvuruları 2027 İlkbaharına kaydırabilir.",
        "• *Takvim:* Sonuçlar Temmuz 2027'ye sarkar; DS-260 formlarının ilk 48 saat içinde gönderilmesi ve Ankara bekleme sürelerine karşı dosya transferi hayati önem kazanır.",
        "",
        "🔴 *Senaryo C: DV-2027 İptali veya DV-2028 ile Birleştirilme (%25 İhtimal)*",
        "• Temyiz mahkemesi Dışişleri'nin takdir yetkisini onarsa DV-2027 atlanabilir veya 2028 ile birleştirilebilir.",
        "• *B Planı:* Sadece çekilişe bel bağlamayıp EB-2 NIW veya O-1/H-1B vize hazırlıklarını şimdiden devreye sokmalıyız.",
        tailored,
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 *SENİN ŞU AN YAPMAN GEREKEN 4 SOMUT EYLEM:*",
        "1. Pasaportunun geçerlilik tarihini (en az 2028) garantiye al.",
        "2. Biyometrik fotoğrafını `/fotograf` ile önceden test et (portal açıldığında sistem kilitlenir).",
        "3. 16 yaşından itibaren e-Devlet adres ve 10 yıllık SGK dökümünü `/ds260` simülatörüne şimdiden gir.",
        "4. Durumunu `/karne` ile test et ve eksiklerini kapat.",
    ]
    return "\n".join(lines)


# ============================================================================
# 8. 360° GREEN CARD TAM SÜREÇ KILAVUZU (10 FAZLI YAŞAM DÖNGÜSÜ)
# ============================================================================

LIFECYCLE_STAGES = [
    ("1. İlk Başvuru", "DS-5501 Formu, 1$ Harç, 600x600 px Fotoğraf ve Confirmation Number"),
    ("2. Sonuç Açıklanması", "ESC (Entrant Status Check) dvprogram.state.gov üzerinden teyit"),
    ("3. Case Number & Sıra", "Bölge kodu ve sıra numarasına göre mülakat ayı öngörüsü"),
    ("4. DS-260 Göçmen Formu", "CEAC üzerinden 16 yaşından günümüze eksiksiz adres, iş ve güvenlik beyanı"),
    ("5. Resmî Evrak Hazırlığı", "Formül A, Formül B, e-Devlet Adli Sicil, Askerlik ve Apostiller"),
    ("6. 2NL Mektubu & Transfer", "KCC mülakat randevu mektubu ve Ankara yoğunluğuna göre transfer taktikleri"),
    ("7. Unganlar Sağlık Muayenesi", "MMR, Tetanoz, Hepatit B aşıları, akciğer filmi ve onaylı doktor raporu"),
    ("8. Public Charge Kalkanı", "Mülakat memuru karşısında banka birikimi, meslek denklik ve Form I-134 sponsoru"),
    ("9. Konsolosluk Mülakatı", "Birebir memur mülakatı, çapraz sorular, sarı zarf ve 221(g) idari işlem yönetimi"),
    ("10. ABD Girişi & İlk 90 Gün", "POE havalimanı girişi, USCIS $220 harcı, SSN, ehliyet, banka hesabı ve Credit Score"),
]


def get_full_lifecycle_guide(selected_stage: Optional[int] = None) -> str:
    """Comprehensive guide covering the entire Green Card process from A to Z."""
    if selected_stage is not None and 1 <= selected_stage <= len(LIFECYCLE_STAGES):
        idx = selected_stage - 1
        name, summary = LIFECYCLE_STAGES[idx]
        return f"🗺️ *Green Card Yol Haritası: Faz {selected_stage} — {name}*\n\n{summary}\n\nDetaylı soru sormak için doğrudan yazabilirsiniz!"

    lines = [
        "🌐 *360° Green Card Sürecinin Eksiksiz Yol Haritası (10 Aşama)*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "Bir göçmen adayı olarak bilmen gereken tüm adımları senin yerine planladım:\n",
    ]
    for i, (name, desc) in enumerate(LIFECYCLE_STAGES, 1):
        lines.append(f"*{name}*\n_{desc}_\n")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Nasıl İlerlemelisin?* Herhangi bir aşamayı detaylandırmak için doğrudan sohbet edebilirsin (Örn: _'Unganlar sağlık muayenesinde hangi aşılar isteniyor?'_ veya _'DS-260'ta adres boşluğu olursa ne yapmalıyım?'_).",
    ])
    return "\n".join(lines)
