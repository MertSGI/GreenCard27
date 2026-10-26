"""Practical personal daily planning and news notifications."""
from datetime import datetime

def due(profile, date, hour):
    return 9 <= hour < 23 and profile.get("last_daily_digest") != date

def digest(profile, checklist, when, headlines=None):
    checks=profile.get("checklist", {})
    done=sum(bool(checks.get(k)) for k,_ in checklist)
    upcoming=[label for k,label in checklist if not checks.get(k)]
    lines=[
        f"☀️ GREEN CARD KOÇUN • {when:%d.%m.%Y}",
        f"Hazırlık ilerlemesi: {done}/{len(checklist)}",
        "",
        "🎯 BUGÜNKÜ SOMUT ADIMLAR:"
    ]
    if upcoming:
        for i,task in enumerate(upcoming[:2],1):
            lines.append(f"{i}. {task}")
    else:
        lines.append("Tüm maddeler tamam; belge güncelliğini ve resmî ilanları yeniden gözden geçir.")
    lines.extend([
        "", "💡 Önerim: Önce birinci adımı yap, sonra /checklist ile işaretle.",
        "⚖️ Mahkeme takvimi, resmî başvuru ilanı ve portalın fiilen açılması farklı konular.",
        "Resmî duyuru: https://travel.state.gov/en/newsroom/visas/2025/changes-to-2027-dv-program-entry-period.html",
        "Vize düzenleme durumu: https://travel.state.gov/en/newsroom/visas/2025/diversity-visa-issuance-updated-guidance.html",
    ])
    if headlines:
        lines.extend(["", "📰 İZLEMELİ HABERLER (başlık, resmî teyit gerekir):"])
        for item in headlines[:2]:
            lines.append(f"• {item['title'][:120]}\n{item['link'][:300]}")
    lines.extend(["", "Komutlar: /bugun /ara /durum /checklist /bildirim_test"])
    return "\n".join(lines)[:3750]

def new_headlines(current, seen):
    if not seen:
        return []
    prior=set(seen)
    return [i for i in current if i.get("id") not in prior][:3]
