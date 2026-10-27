"""Smart User Profile Memory for GreenCard27.

Extracts, stores, and presents personal profile facts (profession, education,
target state/city, marital/family status, budget/savings, english level, and
special notes) so the coach tailors all strategic guidance without repetitive questions.
"""
from __future__ import annotations

import re
from typing import Dict, Any, Optional

PROFILE_FIELDS = {
    "meslek": ("💼 Meslek / Alan", "Yazılım Mühendisi, Doktor, Öğretmen vb."),
    "egitim": ("🎓 Eğitim Durumu", "Lisans, Yüksek Lisans, Ön Lisans vb."),
    "hedef_lokasyon": ("📍 Hedef Eyalet / Şehir", "Texas (Austin), Washington (Seattle) vb."),
    "medeni_durum": ("👨‍👩‍👧 Aile & Medeni Durum", "Evli, 1 çocuk / Bekar vb."),
    "butce": ("💵 Bütçe / Birikim", "15.000$ - 20.000$ vb."),
    "ingilizce": ("🗣 İngilizce Seviyesi", "B2, Akıcı, Orta vb."),
    "ek_notlar": ("📝 Özel Notlar & Tercihler", "Eşi hemşire, F-1 geçmişi var vb."),
}

ALIAS_MAP = {
    "meslek": "meslek",
    "is": "meslek",
    "iş": "meslek",
    "job": "meslek",
    "profession": "meslek",
    "alan": "meslek",
    "egitim": "egitim",
    "eğitim": "egitim",
    "mezuniyet": "egitim",
    "okul": "egitim",
    "degree": "egitim",
    "education": "egitim",
    "hedef": "hedef_lokasyon",
    "eyalet": "hedef_lokasyon",
    "sehir": "hedef_lokasyon",
    "şehir": "hedef_lokasyon",
    "lokasyon": "hedef_lokasyon",
    "yerlesim": "hedef_lokasyon",
    "yerleşim": "hedef_lokasyon",
    "target": "hedef_lokasyon",
    "location": "hedef_lokasyon",
    "state": "hedef_lokasyon",
    "city": "hedef_lokasyon",
    "medeni": "medeni_durum",
    "aile": "medeni_durum",
    "evlilik": "medeni_durum",
    "cocuk": "medeni_durum",
    "çocuk": "medeni_durum",
    "es": "medeni_durum",
    "eş": "medeni_durum",
    "family": "medeni_durum",
    "marital": "medeni_durum",
    "butce": "butce",
    "bütçe": "butce",
    "birikim": "butce",
    "para": "butce",
    "meblag": "butce",
    "meblağ": "butce",
    "budget": "butce",
    "savings": "butce",
    "ingilizce": "ingilizce",
    "dil": "ingilizce",
    "english": "ingilizce",
    "language": "ingilizce",
    "not": "ek_notlar",
    "ek": "ek_notlar",
    "ozel": "ek_notlar",
    "özel": "ek_notlar",
    "notlar": "ek_notlar",
    "ek_notlar": "ek_notlar",
    "notes": "ek_notlar",
}

US_LOCATIONS = [
    "texas", "teksas", "austin", "dallas", "houston", "san antonio",
    "california", "kaliforniya", "los angeles", "san francisco", "san diego", "silicon valley", "silikon vadisi",
    "washington", "seattle",
    "florida", "miami", "orlando", "tampa",
    "new york", "nyc", "manhattan", "brooklyn",
    "illinois", "chicago",
    "massachusetts", "boston",
    "north carolina", "kuzey karolina", "charlotte", "raleigh",
    "georgia", "atlanta",
    "colorado", "denver",
    "virginia", "ohio", "new jersey", "pennsylvania", "arizona", "phoenix",
]

NON_PROFESSION_WORDS = {
    "iyi", "kötü", "hazır", "burada", "türk", "aday", "yolcu", "insan",
    "biri", "emin", "kararlı", "meraklı", "yeni", "eski", "başvuran",
}


def normalize_field_name(alias: str) -> Optional[str]:
    clean = (alias or "").strip().lower()
    return ALIAS_MAP.get(clean)


def extract_profile_facts(text: str) -> Dict[str, str]:
    """Extract profile-worthy facts from natural Turkish sentences."""
    if not text or len(text.strip()) < 4:
        return {}

    found: Dict[str, str] = {}
    lower = text.lower()

    # 1. Bütçe / Birikim (Budget)
    budget_patterns = [
        r"(?:(\d+[\d.,]*)\s*(?:bin|k)?\s*(?:dolar|usd|\$|euro|eur|tl))\s*(?:birikim|bütçe|param|nakit)?",
        r"(?:birikim(?:im|imiz)?|bütçe(?:m|miz)?|param(?:ız)?)\s*(?:yaklaşık|tahmini|ortalama)?\s*[:=]?\s*([\$€]?\s*\d+[\d.,]*\s*(?:bin|k)?\s*(?:dolar|usd|\$|euro|eur|tl)?)",
    ]
    for pat in budget_patterns:
        m = re.search(pat, lower)
        if m:
            val = m.group(0).strip("., ")
            # Temizleme ve netleştirme
            if any(char.isdigit() for char in val):
                found["butce"] = val
                break

    # 2. Medeni Durum ve Çocuklar
    family_parts = []
    is_married = bool(re.search(r"\bevli(?:yim|yiz)?\b", lower))
    spouse_match = re.search(r"eşim\s+([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{3,25}?)(?:dir|dır|dur|dür|'dir|'dır)?(?:\b|,|\.|\s+ve)", lower)

    if is_married or spouse_match:
        if spouse_match:
            sp_job = spouse_match.group(1).strip()
            if sp_job and sp_job not in NON_PROFESSION_WORDS:
                family_parts.append(f"Evli (Eşi {sp_job.title()})")
            else:
                family_parts.append("Evli")
        else:
            family_parts.append("Evli")
    elif re.search(r"\bbekar(?:ım)?\b", lower):
        family_parts.append("Bekar")

    child_match = re.search(r"(\d+)\s*çocu(?:ğum|ğumuz|k)\s*var", lower)
    if child_match:
        family_parts.append(f"{child_match.group(1)} Çocuk")
    elif "çocuğum yok" in lower or "çocuk yok" in lower:
        family_parts.append("Çocuksuz")

    if family_parts:
        found["medeni_durum"] = ", ".join(family_parts)

    # 3. Meslek / Alan
    prof_patterns = [
        r"(?:mesleğim|işim|unvanım)\s*[:=]?\s*([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{3,30}?)(?:\b|,|\.|$)",
        r"(?:\bben\s+)?([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{3,25})\s+olarak\s+çalışıyorum",
        r"\bben\s+(?:(?:\d+\s*(?:yaşında|yaşındayım)[\s,]*)?)([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{3,30}?)(?:yım|yim|yum|yüm|ım|im|um|üm)\b",
        r"\b([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{2,25}?\s*mühendis)(?:iyim|im)\b",
        r"\b([a-zA-ZçğıöşüÇĞİÖŞÜ\s]{2,25}?\s*uzman)(?:ıyım|ım)\b",
    ]
    for pat in prof_patterns:
        m = re.search(pat, lower)
        if m:
            candidate = m.group(1).strip()
            # Yaş veya gereksiz zarfları ayıkla (ör. "32 yaşında kıdemli yazılımcı")
            candidate = re.sub(r"^\d+\s*yaşında\s*", "", candidate).strip()
            # Başta kalan "ben " temizle
            if candidate.lower().startswith("ben "):
                candidate = candidate[4:].strip()
            if candidate.lower().endswith("mühendis"):
                candidate += "i"
            elif candidate.lower().endswith("uzman"):
                candidate += "ı"
            first_word = candidate.split()[0] if candidate else ""
            if candidate and first_word not in NON_PROFESSION_WORDS and len(candidate) > 2:
                # Çok uzun cümleleri kes
                if len(candidate.split()) <= 4:
                    found["meslek"] = candidate.title()
                    break

    # 4. Hedef Lokasyon (Eyalet / Şehir)
    found_locs = []
    for loc in US_LOCATIONS:
        # Kelime sınırıyla ara
        if re.search(rf"\b{re.escape(loc)}\b", lower):
            loc_disp = loc.title()
            if loc in ("nyc", "usa"):
                loc_disp = loc.upper()
            if loc == "teksas":
                loc_disp = "Texas"
            if loc == "kaliforniya":
                loc_disp = "California"
            if loc_disp not in found_locs:
                found_locs.append(loc_disp)

    # Lokasyon bağlamı var mı kontrol et (düşünüyorum, hedefim, gitmek vb.)
    loc_context = any(
        kw in lower for kw in (
            "düşün", "hedef", "gitmek", "yerleş", "eyalet", "şehir", "yaşamak",
            "istiyorum", "istiyoruz", "tarafları", "bölgesi"
        )
    )
    if found_locs and (loc_context or len(found_locs) >= 2 or "hedef" in lower):
        found["hedef_lokasyon"] = " / ".join(found_locs[:3])

    # 5. Eğitim Durumu
    edu_match = re.search(r"\b(lisans|yüksek lisans|doktora|ön lisans|önlisans|master|üniversite|lise)\s*(?:mezunuyum|mezunu|yaptım|öğrencisiyim)?\b", lower)
    if edu_match and ("mezun" in lower or "yaptım" in lower or "okul" in lower or "eğitim" in lower or "diploma" in lower):
        deg = edu_match.group(1).title()
        found["egitim"] = deg

    # 6. İngilizce Seviyesi
    eng_match = re.search(r"\b(?:ingilizce(?:m)?|dil)\s*[:=]?\s*(a1|a2|b1|b2|c1|c2|orta|iyi|akıcı|başlangıç|ileri)\b", lower)
    if eng_match:
        found["ingilizce"] = eng_match.group(1).upper() if len(eng_match.group(1)) == 2 else eng_match.group(1).title()
    elif re.search(r"\b(b1|b2|c1|c2)\s+(?:seviye|düzey)\s*(?:ingilizce)?\b", lower):
        m = re.search(r"\b(b1|b2|c1|c2)\b", lower)
        if m:
            found["ingilizce"] = m.group(1).upper()

    return found


def update_user_facts(existing_facts: Dict[str, str], new_facts: Dict[str, str]) -> bool:
    """Merge new extracted facts into existing facts. Return True if any fact was added/changed."""
    changed = False
    for k, v in new_facts.items():
        if not v or not v.strip():
            continue
        v_clean = v.strip()
        if existing_facts.get(k) != v_clean:
            existing_facts[k] = v_clean
            changed = True
    return changed


def set_profile_field(facts: Dict[str, str], field_or_alias: str, value: str) -> Optional[str]:
    """Manually update a single profile field. Returns canonical key on success, None on invalid field."""
    canon = normalize_field_name(field_or_alias)
    if not canon:
        return None
    facts[canon] = value.strip()
    return canon


def clear_profile_facts(profile: Dict[str, Any]) -> None:
    """Clear all stored personal profile facts."""
    profile["user_facts"] = {}


def format_profile_view(facts: Dict[str, str]) -> str:
    """Generate Markdown text for /profilim Telegram command."""
    lines = [
        "👤 *Akıllı Kişisel Danışman Profil Hafızan*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    has_any = False
    for key, (label, placeholder) in PROFILE_FIELDS.items():
        val = facts.get(key, "").strip()
        if val:
            lines.append(f"{label}: *{val}*")
            has_any = True
        else:
            lines.append(f"{label}: _Belirtilmedi_")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if not has_any:
        lines.append(
            "💡 *Henüz profilinizde kayıtlı bilgi yok.*\n"
            "Sohbet ederken mesleğinizden, bütçenizden, ailenizden veya gitmek istediğiniz "
            "eyaletten bahsettiğinizde sizi otomatik hatırlarım.\n\n"
            "Dilerseniz kendinizi tanıtarak başlayabilirsiniz:\n"
            "_Örn: 'Ben yazılımcıyım, evliyim 1 çocuğum var, bütçemiz 20 bin dolar, Texas düşünüyoruz.'_"
        )
    else:
        lines.append(
            "🎯 *Nasıl Kullanılır?*\n"
            "Bu bilgileri hafızamda tutarak tüm iş piyasası, eyalet, yaşam maliyeti ve vize "
            "analizlerimi doğrudan senin durumuna özel hazırlarım.\n\n"
            "• *Manuel Güncelleme:* `/profil <alan> <bilgi>`\n"
            "  _(Örn: `/profil butce 25.000$` veya `/profil hedef Austin, Texas`)_\n"
            "• *Hafızayı Sıfırlama:* `/profil_temizle`"
        )
    return "\n".join(lines)


def format_profile_for_prompt(facts: Dict[str, str]) -> str:
    """Generate concise context block for Gemini system prompt."""
    if not facts:
        return ""
    entries = []
    for key, (label, _) in PROFILE_FIELDS.items():
        val = facts.get(key, "").strip()
        if val:
            entries.append(f"- {label.split()[1] if len(label.split()) > 1 else label}: {val}")
    if not entries:
        return ""
    return "\n".join(entries)
