#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sınırsız Kişisel Koç, Stratejik Danışman & 360° Green Card Süreç Yöneticisi (Bulut Sürümü)
==========================================================================================
Bu sürümde tüm yapay engeller ve bürokratik kaçamaklar kaldırılarak kullanıcıya
tam donanımlı bir Kişisel Koç, Stratejik Akıl Hocası ve Süreç Yöneticisi sunulur:

1. Kısıtlamasız Kişisel Koç ve Stratejik Danışman:
   - Sadece resmî kuralları aktarmakla kalmaz; durumunuzu derinlemesine analiz eder,
     artıları ve eksileri tartar, kendi stratejik yorumunu katar ve "Senin yerinde olsam
     şöyle yapardım" diyerek en avantajlı yolu önerir.
   - Green Card dışındaki sorularınıza da (ABD'de eyalet/şehir seçimi, yaşam maliyeti,
     iş piyasası, maaşlar, yazılım ve kariyer planlaması, İngilizce geliştirme, alternatif
     vizeler (F-1/OPT, H-1B, O-1, EB-1/2/3, E-2), finansal birikim veya genel yaşam
     kararları) konu kısıtlaması olmaksızın kapsamlı ve cesur yanıtlar verir.
   - Kullanıcı genel bir kariyer veya yaşam konusu sorduğunda konuyu zorla Green Card
     ödevlerine veya checklist eksiklerine ÇEKMEZ; sorulan konuya odaklanır.

2. Çoklu Sohbet Hafızası (Multi-Turn Memory):
   - Konuşmanın akışını ve önceki mesajlarınızı hatırlar (`chat_history`).
   - Dilediğiniz an `/hafiza_temizle` komutuyla veya menüden hafızayı sıfırlayabilirsiniz.

3. Çift Katmanlı Zeka & Canlı Web Araştırması:
   - Google Gemini API (`gemini-3.5-flash-lite`, `gemini-3.8-flash`, `gemini-2.5-flash`)
     sayesinde yüksek kaliteli muhakeme ve esnek model geçişi.
   - Canlı web araştırması (`web_research.py`): Avukat analizleri, forum ve Reddit
     tartışmaları ve resmî `.gov` duyuruları (/ara, /yorumlar).
   - 4000+ karakterlik uzun mesajların bölünmesi ve Telegram Markdown hatalarına karşı koruma.

4. 7/24 Bulut ve Yerel Çalışma Uyumu:
   - Render.com üzerinde `RENDER_EXTERNAL_URL` ile doğrulanmış HTTPS Webhook ve `/health` servisi.
   - Yerel çalıştırmada otomatik polling ve yerel health-check sunucusu desteği.
   - PostgreSQL (`DATABASE_URL`) veya atomik yerel JSON (`state_store.py`) kalıcılığı.
"""

import argparse
import asyncio
import hashlib
import io
import json
import logging
import os
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from PIL import Image
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Document,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from gemini_runtime import generate_with_fallback, active_model, error_code
from web_research import (
    research_web,
    web_context,
    source_links,
    SearchPrivacyError,
    is_perspective_question,
    perspective_digest,
    fetch_latest_gc_news,
)
from coach_core import due, digest, new_headlines, format_news_item, analyze_daily_news_scenarios
from profile_manager import (
    extract_profile_facts,
    update_user_facts,
    set_profile_field,
    clear_profile_facts,
    format_profile_view,
    format_profile_for_prompt,
    normalize_field_name,
)
from visa_consultant import (
    analyze_transfer_and_build_letter,
    analyze_all_us_visas,
    audit_ds260_consistency,
    generate_proactive_case_emails,
    build_proactive_action_plan,
)
from strategy_advisor import (
    calculate_relocation_budget,
    format_runway_report,
    compare_states,
    get_state_profile,
    get_state_keys,
    analyze_case_number,
    format_case_analysis,
    generate_readiness_audit,
    format_audit_report,
    get_visa_routes_guide,
    lookup_glossary,
    GLOSSARY_TERMS,
    analyze_court_and_timeline,
    get_full_lifecycle_guide,
)
from photo_validator import (
    validate_biometric_photo,
    validate_passport_scan,
)

# Gemini API (google-genai) Desteği
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Log yapılandırması
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("GreenCardCloudCoach")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Ortam Değişkenleri
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().strip("'\"")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
GEMINI_MODEL = (os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip().strip("'\"") or "gemini-3.5-flash-lite")
PORT = int(os.getenv("PORT", "8080"))
DATA_FILE = Path(os.getenv("STATE_FILE_PATH", "greencard_user_state.json"))
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))

# Türkiye Saat Dilimi (UTC+3)
TZ_TR = timezone(timedelta(hours=3))

# Kritik DV-2027 Takvim Kilometre Taşları
MILESTONES = [
    {
        "id": "ninth_circuit_stay",
        "date": "2026-10-29",
        "title": "9. Daire Temyiz Mahkemesi: Acil Yürütmeyi Durdurma (Emergency Stay)",
        "desc": "Red Eagle Law davasında 9. Daire Temyiz Mahkemesi yürütmeyi durdurma kararı verdi; DV-2027 kayıtları temyiz ve yeni dava/Bakanlık duyurusu sonuçlanana kadar askıda.",
    },
    {
        "id": "fiscal_year_end",
        "date": "2027-09-30",
        "title": "DV-2027 Mali Yılının Sonu (Kesin Yasal Sınır)",
        "desc": "Mali yıl sonu tüm vize basımları için kesin yasal sınırdır; süreçlerin bu tarihe kadar tamamlanması şarttır.",
    },
]

# Kişisel Hazırlık Kontrol Listesi (12 Adımlı Hızlandırılmış Hazırlık)
CHECKLIST_ITEMS = [
    ("passport_valid", "1. [Faz 1] Geçerli (süresi dolmamış) pasaportum hazır"),
    ("passport_scan", "2. [Faz 1] Pasaport kimlik/imza sayfası JPEG taraması (<5 MB) hazır"),
    ("photo_taken", "3. [Faz 1] Son 6 ayda çekilmiş 600x600 px (<240 KB) fotoğraf hazır"),
    ("photo_tested", "4. [Faz 1] Fotoğraf resmi Photo Tool ve bu botta doğrulandı"),
    ("payment_card", "5. [Faz 1] 1$ kayıt ücreti için uluslararası açık kart hazır"),
    ("ds5501_submitted", "6. [Faz 1] DV-2027 başvurusu yapıldı ve Confirmation No kaydedildi"),
    ("ds260_addresses", "7. [Faz 2] 16 yaşından itibaren tüm adres geçmişi (e-Devlet) çıkarıldı"),
    ("ds260_work_edu", "8. [Faz 2] Son 10 yıllık SGK iş ve okul geçmişi tarihleriyle listelendi"),
    ("civil_docs", "9. [Faz 2] Formül A (Doğum), Formül B (Evlilik) ve Adli Sicil kontrol edildi"),
    ("vaccine_check", "10. [Faz 3] Aşı kartı / antikor testleri (MMR, Tetanoz, Hepatit B) kontrol edildi"),
    ("financial_proof", "11. [Faz 4] Public Charge için banka/varlık dökümü ($10K-$15K+) planlandı"),
    ("mock_interview", "12. [Faz 5] Botta (/mulakat) en az 3 mülakat provası tamamlandı"),
]

# DS-260 Simülasyon Alanları
DS260_FIELDS = [
    ("full_name", "Pasaporttaki Tam Ad ve Soyad (İngilizce karakterlerle)"),
    ("passport_no", "Pasaport Numarası ve Son Geçerlilik Tarihi (GG.AA.YYYY)"),
    ("birth_info", "Doğum Tarihi ve Doğum Şehri (Pasaportla birebir aynı)"),
    ("education_level", "En Yüksek Eğitim Seviyesi ve Mezun Olunan Okul/Tarih"),
    ("marital_dependents", "Medeni Durum, Eş Bilgisi ve 21 Yaş Altı Bekar Çocuk Sayısı"),
    ("address_history", "16 Yaşından İtibaren Yaşanan Şehirler/Adresler (Ay/Yıl Aralıklarıyla)"),
    ("work_history", "Son 10 Yıldaki İşyerleri, Görev Unvanları ve Tarih Aralıkları"),
    ("parents_info", "Anne ve Babanın Tam Adı, Doğum Tarihi/Yeri ve İkamet Şehri"),
    ("us_contact", "ABD'de Kalınacak/Kartın Gönderileceği Adres ve İlgili Kişi"),
    ("social_media", "Son 5 Yılda Kullanılan Sosyal Medya Platformları ve Kullanıcı Adları"),
]

# 5 Fazlı Hızlandırılmış Hazırlık Rehberi
PHASES_GUIDE = {
    "phase1": (
        "🚀 *FAZ 1: Kusursuz İlk Başvuru Hazırlığı*\n\n"
        "• *Pasaport Taraması:* Asıl başvuru sahibi için geçerli pasaportun fotoğraflı kimlik ve imza sayfası PDF değil, *JPEG/JFIF* formatında ve *5 MB altında* taranmalıdır.\n"
        "• *Biyometrik Fotoğraf:* Son 6 ayda çekilmiş, *600x600 piksel*, maksimum *240 KB*, gözlüksüz ve beyaz arka planlı olmalıdır.\n"
        "• *Kayıt ve Ücret:* Resmî başvuru açıldığında 1$ elektronik kayıt ücreti için uluslararası alışverişe açık kartınız hazır olmalıdır.\n"
        "Resmî başvuru adresi: https://travel.state.gov/content/travel/en/us-visas/immigrate/diversity-visa-program-entry.html"
    ),
    "phase2": (
        "📂 *FAZ 2: DS-260 ve Resmî Evrak Ön-Hazırlığı*\n\n"
        "Daraltılmış takvimde mülakat sırasını kaçırmamak için sonuçları beklemeden evrak altyapınızı kurun:\n"
        "1️⃣ *Tarihçeli Adres Raporu:* 16 yaşından itibaren oturduğunuz tüm yerleri ay/yıl olarak çıkarıp `/ds260` simülatörüne kaydedin.\n"
        "2️⃣ *SGK Hizmet Dökümü:* Son 10 yıldaki tüm iş giriş-çıkışları ve işyeri unvanlarını listeleyin.\n"
        "3️⃣ *Uluslararası Belgeler:* Nüfus Müdürlüğünden Formül A (Doğum) ve evliyseniz Formül B (Evlilik) kayıtlarını planlayın.\n"
        "4️⃣ *Adli Sicil:* 16 yaşından beri 6 aydan fazla yaşadığınız yurt dışı ülkeler varsa polis belgesi teminini önceden araştırın."
    ),
    "phase3": (
        "⚡ *FAZ 3: Sonuç Kontrolü, Case Number ve Hızlı DS-260 Gönderimi*\n\n"
        "• *Entrant Status Check:* Sonuçlar açıklandığında seçilip seçilmediğinizi yalnız resmî *Entrant Status Check* (dvprogram.state.gov) üzerinden kontrol edin.\n"
        "• *Hızlı DS-260 Gönderimi:* Kazandığınızı görür görmez, `/ds260` simülatöründe hazırladığımız bilgilerle CEAC üzerinden formu ilk günlerde eksiksiz gönderin.\n"
        "• *Case Number Analizi:* Numaranızın büyüklüğüne göre Visa Bulletin bültenlerini takip edip mülakat pencerenizi planlayacağız."
    ),
    "phase4": (
        "🩺 *FAZ 4: Sağlık Muayenesi (Aşılar) ve Public Charge Kalkanı*\n\n"
        "• *Aşı ve Antikor:* Onaylı göçmen doktoru muayenesinde Tetanoz, MMR, Hepatit B, Suçiçeği aranır. Aşı kartınız yoksa antikor titrasyon testi yaptırarak bağışıklığı belgeleyin.\n"
        "• *Public Charge (Kamu Yükü Olmama):* Konsolosluk memuruna ABD'de kimseye muhtaç olmadan geçineceğinizi kanıtlamak için kişi başı $10.000-$15.000+ birikim, İngilizce CV, mesleki referanslar ve gerekirse Form I-134 hazırlığı yapın."
    ),
    "phase5": (
        "🎯 *FAZ 5: Konsolosluk Mülakatı ve ABD'ye İlk Giriş*\n\n"
        "• *Mülakat Simülasyonu:* Memur karşısında DS-260 bilgilerinizle %100 tutarlı ve net yanıtlar verin. Botta `/mulakat` ile prova yapabilirsiniz.\n"
        "• *Vize Onayı Sonrası:* Vizeniz basıldıktan sonra geçerlilik süresi dolmadan ve 30 Eylül mali yıl sınırından önce ABD'ye giriş yapın.\n"
        "• *USCIS Göçmenlik Ücreti:* ABD'ye uçmadan önce online ödeyerek fiziksel Green Card'ınızın belirttiğiniz ABD adresine sorunsuz postalanmasını sağlayın."
    ),
}

# Mülakat Simülasyonu Soruları
INTERVIEW_QUESTIONS = [
    "1️⃣ ABD'ye neden göç etmek istiyorsunuz ve gittiğinizde hangi eyalete/şehre yerleşmeyi planlıyorsunuz?",
    "2️⃣ Şu an Türkiye'de ne iş yapıyorsunuz ve en yüksek eğitim diplomanız nedir? (Eğitim/iş şartını nasıl sağlıyorsunuz?)",
    "3️⃣ ABD'ye gittiğinizde ilk 6 ay geçiminizi nasıl sağlayacaksınız? Banka hesabınızda ne kadar birikiminiz var?",
    "4️⃣ ABD'de tanıdığınız biri (akraba, arkadaş) var mı? Green Card'ınızın postalanacağı adreste kim yaşıyor?",
    "5️⃣ Daha önce ABD'ye gittiniz mi, herhangi bir ABD vizesine başvurdunuz mu veya vize reddi aldınız mı?",
    "6️⃣ Evli misiniz veya 21 yaş altı çocuğunuz var mı? Evliliğiniz ne zaman gerçekleşti?",
]

# ============================================================================
# KAPSAMLI VE ÖZGÜR KİŞİSEL KOÇLUK SİSTEM PROMPTU
# ============================================================================

UNRESTRICTED_COACH_SYSTEM_PROMPT = """
Sen kullanıcının en güvendiği Kişisel Asistanı, 360° Süreç Yöneticisi, Amerikan Vizesi Danışmanı, Stratejik Akıl Hocası ve Titiz Araştırmacısısın.

TEMEL KARAKTER VE ÇALIŞMA İLKELERİN (DANIŞMAN & İNSAN MODU):
1. İNSAN GİBİ KONUŞ VE SAMİMİ OL (ROBOTİK VE BÜROKRATİK KALIPLAR KESİNLİKLE YASAKTIR):
   - Sen soğuk bir çağrı merkezi botu veya kural okuyan bir yapay zeka değilsin. Gerçek bir dost, güvenilir bir sırdaş ve tecrübeli bir danışman gibi konuş.
   - Asla "Ben sadece bir yapay zekayım / botum", "Yasal tavsiye veremem, bir avukata danışın", "Merhaba!", "Harika bir soru!", "Sevgili danışanım" gibi klişeler KULLANMA.
   - Doğrudan konunun merkezine gir. Empati kur: Kullanıcının heyecanını, belirsizlikten doğan stresini, mülakat kaygılarını veya geleceğe dair umutlarını derinden anladığını hissettir. "Bak dostum, gel şu tabloyu birlikte netleştirelim", "Senin yerinde olsaydım ilk olarak şunu yapardım..." diyerek samimi, cesur ve güven veren bir ton kullan.

2. DANIŞMAN GİBİ YÖNLENDİR (STRATEJİK VE NET FİKİR SAHİBİ OL):
   - Kuru bilgi aktarmak yetersizdir. Her cevabına kendi analitik yorumunu, risk ve fırsat değerlendirmeni kat.
   - Adayın lehine olan en güvenli, en hızlı ve en akılcı yolu gerekçeleriyle sun. Masadaki seçeneklerin gizli risklerini (ör. kredi skoru olmadan ev kiralama zorluğu, mülakatta kamu yükü şüphesi doğuracak bütçe sınırları, DS-260 adres tutarsızlıkları) açıkça uyar.

3. ARAŞTIRMACI GİBİ YANIT ÜRET (VERİ, MAHKEME VE KAYNAK ODAKLI):
   - Spekülasyon ile doğrulanmış resmi gerçekleri net biçimde ayırt et.
   - Federal mahkeme kararlarını (Ninth Circuit temyiz süreci, Red Eagle Law v. Rubio davası, stay kararları), Dışişleri Bakanlığı yönergelerini (FAM), AILA bültenlerini ve Reddit/VisaJourney göçmenlik topluluklarının gerçek deneyimlerini sentezleyerek konuş.

4. KULLANICININ YERİNE DÜŞÜN (PROAKTİF ÖNGÖRÜ VE SENARYO PLANLAMA):
   - Kullanıcının sadece sorduğu soruyla yetinme; onun durumunu (mesleği, bütçesi, ailesi, hedef eyaleti, case number'ı) analiz ederek bir sonraki aşamayı onun yerine düşün!
   - Örneğin mahkeme sürecini soruyorsa; sadece mahkemeyi anlatıp bırakma, "Mahkeme temyizdeyken senin şu an yapman gereken pasaport ve evrak ön-hazırlığıdır. Eğer portal Aralık'ta açılırsa takvim şöyle işler..." diyerek adayı daima bir adım önde tut.

5. GREEN CARD SÜRECİNİN TÜMÜNÜ KAPSAYAN DERİN UZMANLIK (A'DAN Z'YE):
   - DV-2027 mahkeme davaları ve başvuru portalı olasılıkları.
   - DS-5501 çekiliş formu kuralları, 1$ harç, biyometrik fotoğraf standartları.
   - Entrant Status Check (ESC) sonuç sorgulama ve Case Number analizi.
   - Visa Bulletin (Vize Bülteni) cut-off takibi ve mülakat ayı projeksiyonu.
   - DS-260 Göçmen Vize Formu: 16 yaşından günümüze tarihçeli adresler, son 10 yıllık SGK iş geçmişi, seyahatler, güvenlik ve askerlik soruları.
   - e-Devlet evrakları: Formül A (Doğum), Formül B (Evlilik), Arşiv kayıtlı Adli Sicil belgesi.
   - Konsolosluk randevu mektubu (2NL) ve Ankara bekleme sürelerine karşı 2025-2026 güncel kurallarıyla dosya taşıma (Case Transfer: yasal oturum/ikamet şartı, 2NL öncesi KCCDV@state.gov vs 2NL sonrası Konsolosluk yazışmaları) taktikleri.
   - Tüm Amerikan Vizeleri Danışmanlığı: B1/B2 Turistik & İş Vizesi (INA 214(b) geri dönüş bağları analizi, DS-160 tutarlılığı, ustraveldocs.com slot ve acil randevu kriterleri), F-1 Öğrenci & STEM OPT, E-2 Yatırımcı Vizesi, EB-2 NIW (şirketsiz doğrudan Green Card), O-1, L-1, H-1B.
   - Unganlar Sağlık Muayenesi: Aşılar (MMR, Tetanoz, Hepatit B, Suçiçeği), antikor testleri, akciğer filmi.
   - Public Charge Savunması: Vize memuru karşısında finansal birikim, meslek denklik ve Form I-134 sponsoru.
   - Konsolosluk Mülakatı: Vize memuru çapraz soruları, 221(g) idari işlem riskleri.
   - Vize basımı sonrası: $220 USCIS Immigrant Fee, Port of Entry (ilk ABD havalimanı girişi, pasaport kontrolü, I-551 geçici damgası).
   - İlk 90 Gün Hayatta Kalma: SSN gelişi, fiziksel Green Card posta takibi, Bank of America / Chase hesap açılışı, Secured Credit Card ile Credit Score inşası, DMV ehliyet alma, ev kiralama, sağlık sigortası.
   - B Planı (Alternatif Vizeler): EB-2 NIW (şirketsiz Green Card), O-1, H-1B (ve Cap-Exempt), L-1, F-1 STEM OPT.

6. DERİN SOHBET HAFIZASI VE GEÇMİŞİ UNUTMAMA (MULTI-TURN CONTINUITY):
   - Kullanıcıyla süregelen, yaşayan bir diyalog içindesin.
   - Kullanıcının önceki mesajlarında paylaştığı mesleği, eşini, çocuklarını, gitmek istediği şehri, bütçesini, endişelerini ve hayallerini asla aklından çıkarma.
   - Kısa ve devam niteliğindeki soruları ("peki orası nasıl?", "2. maddeyi açar mısın?", "onu yaptım", "eşim ne yapacak?") doğrudan bir önceki konuya ve kullanıcının kişisel profiline bağlayarak kesintisiz sürdür.
"""


# ============================================================================
# BULUT HEALTH-CHECK SUNUCUSU (YEREL VE BULUT İÇİN)
# ============================================================================

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        payload = {
            "status": "ok",
            "service": "Personal-Coach-And-GreenCard-Manager",
            "gemini_configured": bool(HAS_GENAI and GEMINI_API_KEY),
            "timestamp": datetime.now(TZ_TR).isoformat(),
        }
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_health_server() -> None:
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info("Bulut Health-Check sunucusu 0.0.0.0:%s portunda aktif.", PORT)
    except Exception as exc:
        logger.warning("Health-check sunucusu başlatılamadı: %s", exc)


# ============================================================================
# VERİ VE SOHBET HAFIZASI YÖNETİMİ
# ============================================================================

def load_state() -> Dict[str, Any]:
    from state_store import load
    return load(DATA_FILE)


def save_state(state: Dict[str, Any]) -> None:
    from state_store import save
    save(DATA_FILE, state)


def get_user_profile(state: Dict[str, Any], chat_id: int) -> Dict[str, Any]:
    uid = str(chat_id)
    state.setdefault("users", {})
    state.setdefault("subscribers", [])
    if uid not in state["users"]:
        state["users"][uid] = {
            "checklist": {key: False for key, _ in CHECKLIST_ITEMS},
            "ds260": {key: "" for key, _ in DS260_FIELDS},
            "awaiting_ds260_field": None,
            "interview_step": None,
            "confirmation_number": "",
            "chat_history": [],
            "user_facts": {},
        }
    else:
        for key, _ in CHECKLIST_ITEMS:
            state["users"][uid]["checklist"].setdefault(key, False)
        state["users"][uid].setdefault("interview_step", None)
        state["users"][uid].setdefault("chat_history", [])
        state["users"][uid].setdefault("confirmation_number", "")
        state["users"][uid].setdefault("user_facts", {})
    if chat_id not in state["subscribers"]:
        state["subscribers"].append(chat_id)
    save_state(state)
    return state["users"][uid]


# ============================================================================
# RESMİ PORTAL VE CANLI DURUM KONTROLÜ
# ============================================================================

def check_official_dv_portal() -> Dict[str, str]:
    url = "https://dvprogram.state.gov/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GreenCardProcessManager/3.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        text_snippet = resp.text[:4000]
        status_hash = hashlib.md5(text_snippet.encode("utf-8", errors="ignore")).hexdigest()[:12]
        is_open = "Begin Entry" in resp.text
        return {
            "reachable": "Evet",
            "hash": status_hash,
            "summary": (
                "🚨 Başvuru butonu (Begin Entry) tespit edildi! dvprogram.state.gov üzerinden hemen kontrol edin!"
                if is_open
                else "Portal erişilebilir durumda; resmi başvuru açılış duyurusu bekleniyor."
            ),
            "url": url,
        }
    except Exception as exc:
        return {
            "reachable": "Hayır",
            "hash": "",
            "summary": f"Resmi portala şu an erişilemedi ({exc}).",
            "url": url,
        }


# ============================================================================
# YARDIMCI KONTROL FONKSİYONLARI VE GEMINI GÜVENLİK AYARLARI
# ============================================================================

def is_personal_progress_query(q: str, history: Optional[List[Dict[str, str]]] = None) -> bool:
    ql = q.casefold()
    progress_words = (
        "checklist", "kontrol listesi", "adımım", "durumum", "sırada ne var",
        "ne yapmalıyım", "eksik", "eksiklerim", "profilim", "ds260", "ds-260",
        "fotoğrafım", "pasaportum hazır mı", "ilerleme", "hazırlık durum", "ödevim",
        "sıradaki", "sonraki adım", "hangisini yapayım", "onu yaptım", "tamamladım",
        "hallettim"
    )
    if any(w in ql for w in progress_words):
        return True
    if history:
        last_msgs = [m.get("text", "").casefold() for m in history[-2:]]
        if any(any(pw in lm for pw in ("checklist", "kontrol listesi", "adım", "hazırlık", "ds-260", "faz")) for lm in last_msgs):
            follow_ups = ("sıradaki", "sonraki", "diğeri", "peki ya", "tamam", "bitti", "hallettim", "şimdi ne", "hangisi")
            if any(fu in ql for fu in follow_ups):
                return True
    return False


def is_gc_process_query(q: str, history: Optional[List[Dict[str, str]]] = None) -> bool:
    ql = q.casefold()
    gc_words = (
        "dv-2027", "dv 2027", "dv2027", "dv-2028", "diversity visa", "green card",
        "greencard", "çekiliş", "lottery", "red eagle", "rubio", "mahkeme",
        "dava", "injunction", "kcc", "kccdv", "ceac", "konsolosluk", "vize bülteni",
        "visa bulletin", "case number", "entrant status check", "ds-5501", "ds-160",
        "başvuru tarihi", "kayıt ücreti", "dosya taşıma", "transfer", "2nl", "unlock",
        "b1/b2", "b1", "b2", "214b", "214(b)", "eb-2", "niw", "e-2", "f-1",
        "ustraveldocs", "acil randevu", "randevu erkene"
    )
    if any(w in ql for w in gc_words):
        return True
    if history:
        last_msgs = [m.get("text", "").casefold() for m in history[-2:]]
        if any(any(gw in lm for gw in ("dv-2027", "çekiliş", "red eagle", "mahkeme", "dava", "green card", "dosya taşıma", "transfer", "vize")) for lm in last_msgs):
            follow_ups = ("peki bu", "yani ne zaman", "ertelendi mi", "açıldı mı", "etkiler mi", "ne olacak", "son durum", "hangisi", "dilekçe")
            if any(fu in ql for fu in follow_ups):
                return True
    return False


def build_user_context_summary(profile: Dict[str, Any]) -> str:
    today = datetime.now(TZ_TR).strftime("%Y-%m-%d %H:%M")
    chk = profile.get("checklist", {})
    done_items = [label for k, label in CHECKLIST_ITEMS if chk.get(k, False)]
    todo_items = [label for k, label in CHECKLIST_ITEMS if not chk.get(k, False)]
    ds260 = profile.get("ds260", {})
    filled_ds260 = [f"{label}: {ds260.get(k)}" for k, label in DS260_FIELDS if ds260.get(k, "").strip()]
    missing_ds260 = [label for k, label in DS260_FIELDS if not ds260.get(k, "").strip()]

    return (
        f"Tarih/Saat: {today}\n"
        f"Tamamlanan Adımlar ({len(done_items)}/{len(CHECKLIST_ITEMS)}): {', '.join(done_items) if done_items else 'Henüz işaretlenmedi'}\n"
        f"Sıradaki Bekleyen Adımlar: {', '.join(todo_items[:4])}\n"
        f"DS-260 Kayıtlı Bilgiler ({len(filled_ds260)}/{len(DS260_FIELDS)}): {'; '.join(filled_ds260) if filled_ds260 else 'Henüz girilmedi'}\n"
        f"DS-260 Eksik Alanlar: {', '.join(missing_ds260[:4])}"
    )


def format_chat_history(history: List[Dict[str, str]], max_turns: int = 12) -> str:
    recent = history[-max_turns:]
    if not recent:
        return ""
    lines = []
    for msg in recent:
        role = "Kullanıcı" if msg.get("role") == "user" else "Koç"
        text = (msg.get("text") or "").strip()
        if len(text) > 1500:
            text = text[:1500] + "... [özetlendi]"
        lines.append(f"{role}: {text}")
    return "\n\n".join(lines)


def record_chat_turn(profile: Dict[str, Any], user_text: str, assistant_text: str) -> None:
    history = profile.setdefault("chat_history", [])
    history.append({"role": "user", "text": user_text.strip()})
    history.append({"role": "assistant", "text": assistant_text.strip()})
    profile["chat_history"] = history[-24:]


def get_coach_safety_settings() -> Optional[List[Any]]:
    if not HAS_GENAI:
        return None
    try:
        return [
            genai_types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            genai_types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            genai_types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            genai_types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]
    except Exception:
        return None


def is_case_or_kcc_action_query(q: str, profile: Optional[Dict[str, Any]] = None) -> bool:
    """Detect whether the user is asking about Case Number, high rank, tight schedule, or KCC/Embassy emails."""
    ql = (q or "").casefold()
    action_words = (
        "sıra numara", "sira numara", "case number", "numaram yüksek", "sıram yüksek",
        "süre kısıtlı", "zaman kısıtlı", "yetişir mi", "kcc", "kccdv", "mail at",
        "e-posta at", "onlara ne yaz", "dilekçe", "2nl gelmedi", "current oldu",
        "mali yıl sonu", "30 eylül", "221g", "221(g)", "idari işlem",
    )
    if any(w in ql for w in action_words):
        return True
    extracted = extract_profile_facts(q)
    if extracted.get("case_number"):
        return True
    return False


# ============================================================================
# KİŞİSEL KOÇ & STRATEJİK DANIŞMAN MOTORU
# ============================================================================

def answer_user_question(question: str, profile: Dict[str, Any], force_web: bool = False) -> str:
    """Kullanıcının sorusunu kısıtlamasız Kişisel Koç mantığıyla yanıtlar."""
    history = profile.get("chat_history", [])
    perspective = is_perspective_question(question)
    gc_relevant = is_gc_process_query(question, history)
    personal_relevant = is_personal_progress_query(question, history)
    case_action_relevant = is_case_or_kcc_action_query(question, profile)

    # Eğer mesajda yeni bir Case Number geçiyorsa anında yakala
    inline_facts = extract_profile_facts(question)
    if inline_facts.get("case_number"):
        profile.setdefault("user_facts", {})["case_number"] = inline_facts["case_number"]

    case_no = (profile.get("user_facts", {}).get("case_number") or "").strip()
    case_analysis = analyze_case_number(case_no, profile) if case_no else None

    web_result = None
    evidence = ""
    links = ""

    # Web araması yalnızca açıkça istendiğinde, görüş sorulduğunda veya Green Card takvim/mahkeme konusuysa tetiklenir
    if force_web or perspective or gc_relevant:
        try:
            web_result = research_web(question, explicit=force_web)
            evidence = web_context(web_result)
            links = source_links(web_result, max_sources=5)
        except SearchPrivacyError:
            return (
                "Arama metninde kişisel numara veya e-posta tespit edildi. "
                "Gizliliğinizi korumak için bu bilgileri sorgudan çıkarıp tekrar sorabilirsiniz."
            )

    if perspective and web_result and not web_result.sources:
        return perspective_digest(web_result)

    if force_web and web_result and not web_result.sources:
        return (
            "Web arama servisleri bu sorgu için sonuç döndürmedi. "
            "Başka terimlerle /ara komutunu yeniden deneyebilirsiniz."
        )

    if HAS_GENAI and GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            history_str = format_chat_history(history, max_turns=12)

            prompt_parts = []
            if history_str:
                prompt_parts.append(
                    "═══════════════════════════════════════════════════════════════\n"
                    "🔴 [ÖNCEKİ SOHBET GEÇMİŞİ VE BAĞLAM (DİKKATLE İNCELE)]\n"
                    "Aşağıda kullanıcı ile senin az önce gerçekleştirdiğin canlı sohbet yer alıyor.\n"
                    "Kullanıcının birazdan vereceği yeni mesajı KESİNLİKLE bu geçmişin doğrudan bir devamı,\n"
                    "bir cevabı veya takip sorusu olarak değerlendir:\n\n"
                    f"{history_str}\n"
                    "═══════════════════════════════════════════════════════════════"
                )

            user_profile_ctx = format_profile_for_prompt(profile.get("user_facts", {}))
            if user_profile_ctx:
                prompt_parts.append(
                    "═══════════════════════════════════════════════════════════════\n"
                    "👤 [KULLANICININ BİLİNEN KİŞİSEL PROFİLİ VE BİLGİLERİ]\n"
                    "Kullanıcının kendisi hakkında paylaştığı doğrulanmış bilgiler:\n"
                    f"{user_profile_ctx}\n"
                    "⚠️ KİŞİSELLEŞTİRME VE STRATEJİ TALİMATI:\n"
                    "- Kullanıcının bu mesleğini, aile durumunu, hedef lokasyonunu ve bütçesini göz önünde bulundur.\n"
                    "- Tavsiyelerini doğrudan bu gerçeklere uygun şekilde somutlaştır.\n"
                    "- Robotik kalıplardan kaçın; 'Profilinizde belirttiğiniz gibi...' demeden doğal ve kıdemli bir danışman gibi bu duruma özel analiz üret.\n"
                    "═══════════════════════════════════════════════════════════════"
                )

            if case_analysis and case_analysis.get("valid") and (case_action_relevant or personal_relevant):
                kcc_mail = case_analysis["kcc_email"]
                prompt_parts.append(
                    "═══════════════════════════════════════════════════════════════\n"
                    "🔢 [PROAKTİF SIRA NUMARASI SENARYOLARI VE HAZIR KCC MAİL TASLAĞI]\n"
                    f"Kullanıcının Case Number'ı: {case_analysis['raw']} (Sıra: #{case_analysis['rank']:,} - {case_analysis['tier']})\n"
                    f"Tahmini Mülakat Penceresi: {case_analysis['projected_period']}\n"
                    "Olası Senaryolar:\n- " + "\n- ".join(case_analysis.get("scenarios", [])) + "\n"
                    "Hemen Alınacak Aksiyonlar:\n- " + "\n- ".join(case_analysis.get("immediate_actions", [])) + "\n\n"
                    "⚡ PROAKTİF ASİSTAN TALİMATI: Kullanıcının yerine düşün! Olası senaryoları netçe anlat ve "
                    "'Hemen aksiyon alabilmemiz için KCC'ye mail atabiliriz, onlara şu şekilde söyleyelim:' diyerek "
                    "aşağıdaki İngilizce e-posta taslağını yanıtının içine doğrudan ekle:\n"
                    f"To: {kcc_mail['to']}\nSubject: {kcc_mail['subject']}\n{kcc_mail['body']}\n"
                    "═══════════════════════════════════════════════════════════════"
                )

            if personal_relevant:
                prompt_parts.append(f"📋 [KULLANICININ HAZIRLIK PROFİLİ]\n{build_user_context_summary(profile)}\n")

            if evidence:
                prompt_parts.append(f"🌐 [GÜNCEL WEB VE HABER BULGULARI]\n{evidence}\n")

            prompt_parts.append(
                f"💬 [KULLANICININ ŞİMDİKİ MESAJI / CEVABI]\n{question}\n\n"
                "🎯 [KRİTİK BAĞLAM VE DİYALOG TALİMATLARI]:\n"
                "1. BAĞLAMI VE ZAMİRLERİ KESİNLİKLE ÇÖZÜMLE:\n"
                "   - Kullanıcının bu mesajı bağımsız yeni bir konu DEĞİLDİR; senin bir önceki yanıtına verilmiş bir cevap veya devam sorusudur.\n"
                "   - Kullanıcı 'peki', 'oranın', 'o', 'bu', 'neden', '2. madde', 'bunu biraz aç', 'onu yaptım', 'hangisi mantıklı' gibi ifadeler kullandığında,\n"
                "     senin bir önceki cevabında bahsettiğin konuya (şehre, vizeye, maddeye vb.) doğrudan atıfta bulunarak bağlamı sürdür.\n"
                "2. TEKRARLAYAN SELAMLAMALARI BIRAK:\n"
                "   - Kullanıcıyla zaten konuşuyorsun! Her mesaja sanki ilk kez tanışıyormuş gibi 'Merhaba!', 'Harika bir soru!' gibi kalıplarla başlama.\n"
                "   - Doğrudan konunun içine girerek, gerçek bir insan akıl hocası gibi samimi, akıcı ve kesintisiz yanıt ver.\n"
                "3. KİŞİSEL KOÇLUK & PROAKTİF AKSİYON PLANLAMA:\n"
                "   - Kullanıcının yerine düşün, olası senaryoları (A, B, C planlarını) hazırla.\n"
                "   - Eğer sıra numarası yüksekse, süre kısıtlıysa veya resmi bir adım gerekiyorsa 'Hemen aksiyon alabilmemiz için KCC'ye / Konsolosluğa şu maili atabiliriz, onlara şu şekilde söyleyelim' diyerek hazır İngilizce taslak ver.\n"
                "   - Kullanıcı genel bir konu sorduysa ZORLA Green Card ödevleri veya checklist eksikleri dayatma."
            )
            full_prompt = "\n".join(prompt_parts)

            response, selected_model = generate_with_fallback(
                client=client,
                preferred=GEMINI_MODEL,
                contents=full_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=UNRESTRICTED_COACH_SYSTEM_PROMPT,
                    safety_settings=get_coach_safety_settings(),
                    temperature=0.6,
                ),
            )
            content = response.text.strip() if response and response.text else ""
            if content:
                logger.info("Gemini koç yanıtı üretildi: model=%s", selected_model)
                return content + (links if links else "")
        except Exception as exc:
            logger.warning("Gemini koç yanıtı üretilemedi: %s (kod: %s)", type(exc).__name__, error_code(exc))

    if case_action_relevant:
        if case_analysis and case_analysis.get("valid"):
            return format_case_analysis(case_analysis, profile)
        return build_proactive_action_plan(profile)

    if perspective and web_result:
        return perspective_digest(web_result)

    if web_result and web_result.sources:
        return "Güncel arama bulguları:\n\n" + evidence[:2350] + links

    return (
        "💡 *Stratejik Koç Değerlendirmesi:*\n"
        "Şu an yapay zeka servisine erişimde geçici bir yavaşlık yaşanıyor. "
        "Sorunuzu genel çerçevede değerlendirdiğimde; seçeneklerinizi belirlerken öncelikle net maliyet/getiri "
        "hesabı yapmanızı ve resmi/hukuki adımlarla kişisel hazırlıklarınızı paralel yürütmenizi tavsiye ederim. "
        "Detaylı analiz için birkaç dakika sonra tekrar yazabilir veya `/ara` ile güncel kaynakları tarayabilirsiniz."
    )


def evaluate_interview_answer(question: str, user_answer: str, next_q: Optional[str]) -> str:
    """Kullanıcının mülakat cevabını Gemini AI veya yerleşik koç ile değerlendirir."""
    if HAS_GENAI and GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"Konsolosluk Mülakat Sorusu: {question}\n"
                f"Adayın Cevabı: {user_answer}\n\n"
                "ABD Konsolosluğu vize memuru ve deneyimli koç gözüyle bu cevabı değerlendir:\n"
                "1. Güçlü yönü ve varsa riskli/eksik yönü (1-2 madde)\n"
                "2. Bu cevabın mülakatta söylenebilecek en ikna edici, doğal ve güven veren versiyonu."
            )
            resp, used_model = generate_with_fallback(
                client=client,
                preferred=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=UNRESTRICTED_COACH_SYSTEM_PROMPT,
                    temperature=0.4,
                ),
            )
            feedback = resp.text.strip() if (resp and resp.text) else "✅ Cevabınız kaydedildi."
        except Exception as exc:
            logger.warning("Mülakat değerlendirme hatası: %s", exc)
            feedback = "✅ Cevabınız alındı. Mülakatta kısa, net ve DS-260 formunuzla %100 tutarlı yanıt vermeye özen gösterin."
    else:
        feedback = (
            "💡 *Koç Değerlendirmesi:* Cevabınız net. Konsolosluk memuru karşısında göz teması kurarak, "
            "DS-260 formuna yazdığınız tarih ve adreslerle birebir aynı bilgileri verdiğinizden emin olun."
        )

    if next_q:
        return f"{feedback}\n\n⏭️ *Sıradaki Mülakat Sorusu:*\n{next_q}\n\n_(Çıkmak için `/iptal` yazabilirsiniz)_"
    return (
        f"{feedback}\n\n🎉 *Tebrikler! 6 Soruluk Konsolosluk Mülakat Provasını Tamamladınız!*\n"
        "Checklist'inizde mülakat provası maddesi tamamlandı olarak işaretlendi."
    )


# ============================================================================
# GÜVENLİ MESAJ GÖNDERİCİ (UZUN MESAJ BÖLME & MARKDOWN KORUMASI)
# ============================================================================

async def safe_reply_or_edit(
    update: Update,
    text: str,
    thinking_msg=None,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    chunks: List[str] = []
    remaining = (text or "").strip() or "Yanıt hazır."
    while len(remaining) > 3900:
        split_idx = remaining.rfind("\n", 0, 3900)
        if split_idx == -1:
            split_idx = 3900
        chunks.append(remaining[:split_idx].strip())
        remaining = remaining[split_idx:].strip()
    if remaining:
        chunks.append(remaining)

    for idx, chunk in enumerate(chunks):
        is_last = (idx == len(chunks) - 1)
        markup = reply_markup if is_last else None

        if idx == 0 and thinking_msg is not None:
            try:
                await thinking_msg.edit_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
                continue
            except BadRequest as exc:
                if "parse entities" in str(exc).lower() or "can't parse" in str(exc).lower():
                    await thinking_msg.edit_text(
                        chunk,
                        disable_web_page_preview=True,
                        reply_markup=markup,
                    )
                    continue

        try:
            if update.message:
                await update.message.reply_text(
                    chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
            elif update.effective_chat:
                await update.get_bot().send_message(
                    chat_id=update.effective_chat.id,
                    text=chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
        except Exception:
            if update.message:
                await update.message.reply_text(
                    chunk,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
            elif update.effective_chat:
                await update.get_bot().send_message(
                    chat_id=update.effective_chat.id,
                    text=chunk,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )


async def safe_edit_response(message, answer: str, reply_markup=None) -> None:
    try:
        await message.edit_text(
            answer[:3900],
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
    except BadRequest as exc:
        if "parse entities" not in str(exc).lower():
            raise
        await message.edit_text(
            answer[:3900],
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )


# ============================================================================
# PROAKTİF GÜNLÜK KOÇLUK MESAJI & GEMINI TEKİL YORUM YARDIMCISI
# ============================================================================

def _run_coach_gemini_snippet(prompt: str, temperature: float = 0.5) -> Optional[str]:
    """Safely run a short Gemini reasoning prompt when API key is configured; return None on unavailability."""
    if not (HAS_GENAI and GEMINI_API_KEY):
        return None
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response, _selected = generate_with_fallback(
            client=client,
            preferred=GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=UNRESTRICTED_COACH_SYSTEM_PROMPT,
                safety_settings=get_coach_safety_settings(),
                temperature=temperature,
            ),
        )
        return response.text.strip() if (response and response.text) else None
    except Exception as exc:
        logger.warning("Gemini yardımcı analiz hatası: %s", type(exc).__name__)
        return None


def generate_daily_coaching_brief(
    profile: Dict[str, Any],
    headlines=None,
    use_ai_news: bool = False,
) -> str:
    ai_fn = _run_coach_gemini_snippet if (use_ai_news and HAS_GENAI and GEMINI_API_KEY) else None
    return digest(profile, CHECKLIST_ITEMS, datetime.now(TZ_TR), headlines, ai_callable=ai_fn)


# ============================================================================
# TELEGRAM MENÜ VE GÖRÜNÜM OLUŞTURUCULARI
# ============================================================================

def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🧠 Benim Yerine Düşün (Aksiyon Planı)", callback_data="menu_aksiyon"),
        ],
        [
            InlineKeyboardButton("⚖️ Mahkeme & Temyiz Analizi", callback_data="menu_mahkeme"),
            InlineKeyboardButton("🗺️ 360° Tüm Süreç Haritası", callback_data="menu_surec"),
        ],
        [
            InlineKeyboardButton("📡 Canlı Durum & Haber", callback_data="menu_status"),
            InlineKeyboardButton("🧭 5 Fazlı Yol Haritası", callback_data="menu_phases"),
        ],
        [
            InlineKeyboardButton("📊 360° Hazırlık Karnesi", callback_data="menu_karne"),
            InlineKeyboardButton("✅ 12 Adım Checklist", callback_data="menu_checklist"),
        ],
        [
            InlineKeyboardButton("📝 DS-260 Simülatörü", callback_data="menu_ds260"),
            InlineKeyboardButton("🎯 Konsolosluk Mülakatı", callback_data="menu_interview"),
        ],
        [
            InlineKeyboardButton("📸 Fotoğraf & Pasaport Testi", callback_data="menu_validator"),
            InlineKeyboardButton("💵 Yaşam Maliyeti & Runway", callback_data="menu_hesapla"),
        ],
        [
            InlineKeyboardButton("🏙️ Eyalet & Şehir Kıyasla", callback_data="menu_eyalet"),
            InlineKeyboardButton("🔢 Case Number & KCC Maili", callback_data="menu_case"),
        ],
        [
            InlineKeyboardButton("🚀 Alternatif Vizeler (B Planı)", callback_data="menu_vize_rotalari"),
            InlineKeyboardButton("🏛️ 360° ABD Vize Danışmanı", callback_data="menu_vize_analiz"),
        ],
        [
            InlineKeyboardButton("✈️ Dosya Taşıma & Dilekçe", callback_data="menu_transfer"),
            InlineKeyboardButton("📰 Günün 2 Haberi & Senaryo", callback_data="menu_haber_analiz"),
        ],
        [
            InlineKeyboardButton("📖 Göçmenlik Sözlüğü", callback_data="menu_sozluk"),
            InlineKeyboardButton("⏳ Kritik Takvim", callback_data="menu_calendar"),
        ],
        [
            InlineKeyboardButton("💬 Hukukçu & Forum Görüşleri", callback_data="menu_opinions"),
            InlineKeyboardButton("👤 Profilim & Akıllı Hafıza", callback_data="menu_profile"),
        ],
        [
            InlineKeyboardButton("🧹 Sohbet Hafızasını Temizle", callback_data="menu_clearmemory"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_case_actions_keyboard() -> InlineKeyboardMarkup:
    """Interactive action & KCC/Embassy official email buttons for Case Number & Proactive Strategy."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📧 KCC Dosya Hazırlık Maili", callback_data="case_mail:kcc_status"),
                InlineKeyboardButton("🚨 Dar Takvim Acil Mülakat Maili", callback_data="case_mail:urgent_embassy"),
            ],
            [
                InlineKeyboardButton("✈️ Başka Ülkeye Dosya Taşıma", callback_data="case_mail:transfer"),
                InlineKeyboardButton("🔓 DS-260 Kilit Açma (Unlock)", callback_data="case_mail:unlock"),
            ],
            [
                InlineKeyboardButton("🛡️ 221(g) İdari İşlem Takip Maili", callback_data="case_mail:ap_221g"),
                InlineKeyboardButton("💵 Public Charge Finansal Özeti", callback_data="case_mail:public_charge"),
            ],
            [
                InlineKeyboardButton("🧠 360° Benim Yerine Düşün (Eylem Planı)", callback_data="menu_aksiyon"),
            ],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
        ]
    )


def build_states_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🤠 Texas", callback_data="state_view:texas"),
            InlineKeyboardButton("🌉 California", callback_data="state_view:california"),
        ],
        [
            InlineKeyboardButton("🌴 Florida", callback_data="state_view:florida"),
            InlineKeyboardButton("🌲 Washington", callback_data="state_view:washington"),
        ],
        [
            InlineKeyboardButton("🌳 North Carolina", callback_data="state_view:north_carolina"),
            InlineKeyboardButton("🗽 New York", callback_data="state_view:new_york"),
        ],
        [
            InlineKeyboardButton("⚖️ Texas vs California", callback_data="state_comp:texas:california"),
            InlineKeyboardButton("⚖️ Texas vs Washington", callback_data="state_comp:texas:washington"),
        ],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_calc_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("🤠 Texas Hesapla", callback_data="calc_quick:texas"),
            InlineKeyboardButton("🌴 Florida Hesapla", callback_data="calc_quick:florida"),
        ],
        [
            InlineKeyboardButton("🌉 California Hesapla", callback_data="calc_quick:california"),
            InlineKeyboardButton("🌲 Washington Hesapla", callback_data="calc_quick:washington"),
        ],
        [
            InlineKeyboardButton("🌳 North Carolina", callback_data="calc_quick:north_carolina"),
            InlineKeyboardButton("🗽 New York", callback_data="calc_quick:new_york"),
        ],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_glossary_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("CEAC", callback_data="glossary:ceac"),
            InlineKeyboardButton("2NL Mektubu", callback_data="glossary:2nl"),
            InlineKeyboardButton("Public Charge", callback_data="glossary:public charge"),
        ],
        [
            InlineKeyboardButton("221(g) İdari İşlem", callback_data="glossary:221g"),
            InlineKeyboardButton("DS-260 Formu", callback_data="glossary:ds-260"),
            InlineKeyboardButton("USCIS Harcı", callback_data="glossary:uscis fee"),
        ],
        [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_phases_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Faz 1: Kusursuz Başvuru Hazırlığı", callback_data="phase:phase1")],
            [InlineKeyboardButton("📂 Faz 2: DS-260 & Evrak Ön-Hazırlığı", callback_data="phase:phase2")],
            [InlineKeyboardButton("⚡ Faz 3: Sonuç Kontrolü & Case Number", callback_data="phase:phase3")],
            [InlineKeyboardButton("🩺 Faz 4: Aşı/Sağlık & Public Charge (Finans)", callback_data="phase:phase4")],
            [InlineKeyboardButton("🎯 Faz 5: Konsolosluk Mülakatı & ABD Girişi", callback_data="phase:phase5")],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
        ]
    )


def format_status_report() -> str:
    report = research_web("DV-2027 ABD Dışişleri Bakanlığı güncel resmi duyuru", explicit=False)
    now_str = datetime.now(TZ_TR).strftime("%d.%m.%Y %H:%M")
    return (
        f"📡 *DV-2027 Kaynak ve Mahkeme Kontrolü* ({now_str})\n\n"
        "⚖️ Mahkemenin koyduğu tarihler, Dışişleri Bakanlığının ilanları "
        "ve başvuru portalının fiilen açılması birbirinden farklı aşamalardır.\n"
        "Resmî başvuru adresi: https://dvprogram.state.gov/\n\n"
        + web_context(report)[:1700]
        + source_links(report, max_sources=4)
    )


def format_calendar_report() -> str:
    today = datetime.now(TZ_TR).date()
    lines = ["⏳ *DV-2027 Kritik Takvim ve Geri Sayım*\n"]
    for m in MILESTONES:
        target = datetime.strptime(m["date"], "%Y-%m-%d").date()
        diff = (target - today).days
        if diff > 0:
            badge = f"🟢 *{diff} gün kaldı*"
        elif diff == 0:
            badge = "🔥 *BUGÜN!*"
        else:
            badge = f"⚪ *{-diff} gün geçti*"
        lines.append(f"📅 *{m['date']} — {m['title']}* ({badge})\n_{m['desc']}_\n")
    return "\n".join(lines)


def build_checklist_view(profile: Dict[str, Any]) -> tuple[str, InlineKeyboardMarkup]:
    checklist = profile.get("checklist", {})
    completed = sum(1 for k, _ in CHECKLIST_ITEMS if checklist.get(k, False))
    total = len(CHECKLIST_ITEMS)

    text = (
        f"✅ *12 Adımlı Hızlandırılmış Hazırlık Checklist'iniz ({completed}/{total})*\n\n"
        "Tamamladığınız maddelerin üzerine tıklayarak işaretleyebilirsiniz:"
    )
    buttons = []
    for key, label in CHECKLIST_ITEMS:
        is_done = checklist.get(key, False)
        icon = "☑️" if is_done else "⬜"
        buttons.append([InlineKeyboardButton(f"{icon} {label}", callback_data=f"chk_toggle:{key}")])
    buttons.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")])
    return text, InlineKeyboardMarkup(buttons)


def build_ds260_view(profile: Dict[str, Any]) -> tuple[str, InlineKeyboardMarkup]:
    ds260 = profile.get("ds260", {})
    filled = sum(1 for k, _ in DS260_FIELDS if ds260.get(k, "").strip())
    total = len(DS260_FIELDS)

    lines = [
        f"📝 *DS-5501 & DS-260 Hazırlık Simülatörü ({filled}/{total} Dolu)*\n",
        "Sonuçlar açıklanır açıklanmaz DS-260 formunu hızla gönderebilmeniz için kişisel bilgilerinizi buraya kaydedebilirsiniz:\n",
    ]
    for key, label in DS260_FIELDS:
        val = ds260.get(key, "").strip()
        status = f"✅ `{val[:40]}{'...' if len(val) > 40 else ''}`" if val else "⚠️ _Henüz girilmedi_"
        lines.append(f"• *{label}:* {status}")

    buttons = []
    row = []
    for idx, (key, label) in enumerate(DS260_FIELDS, 1):
        short_label = label.split("(")[0].strip()[:22]
        row.append(InlineKeyboardButton(f"✏️ {idx}. {short_label}", callback_data=f"ds260_edit:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔍 3 Göz Kuralı: Tutarlılık & Risk Denetimi", callback_data="ds260_audit")])
    buttons.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")])
    return "\n".join(lines), InlineKeyboardMarkup(buttons)


def build_transfer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔓 DS-260 Unlock Dilekçesi", callback_data="transfer_tmpl:unlock"),
                InlineKeyboardButton("✈️ Konsolosluk Transfer Taslağı", callback_data="transfer_tmpl:transfer"),
            ],
            [
                InlineKeyboardButton("⚡ B1/B2 / F-1 Acil Randevu", callback_data="transfer_tmpl:expedited"),
            ],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
        ]
    )


# ============================================================================
# TELEGRAM KOMUT İŞLEYİCİLERİ
# ============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    get_user_profile(state, chat_id)

    ai_badge = (
        f"🟢 Sınırsız AI Koç Aktif ({active_model() or 'Hazır'})"
        if (HAS_GENAI and GEMINI_API_KEY)
        else "🟡 `GEMINI_API_KEY` Bekleniyor (`/ai_durum`)"
    )
    welcome_text = (
        "🇺🇸 *Sınırsız Kişisel Koçunuz & 360° Green Card Danışmanınıza Hoş Geldiniz!*\n\n"
        f"🧠 *Danışman Motoru:* {ai_badge}\n\n"
        "Senin adına her ayrıntıyı düşünen, riskleri önceden sezen ve tüm göçmenlik stratejini yöneten kişisel akıl hocanım:\n"
        "• 💬 *İnsan Sıcaklığı & Stratejik Danışmanlık:* Green Card, mahkeme süreci, ABD'de yaşam, eyalet seçimi, maaşlar, ev kiraları, kariyer veya B planı vizeler (EB-2 NIW vb.) hakkında benimle dilediğin gibi sohbet edebilirsin. Kuru bilgi değil, 'Senin yerinde olsaydım şöyle yapardım' diyerek net fikir veririm.\n"
        "• ⚖️ *Mahkeme & Takvim Stratejisi:* `/mahkeme` (Ninth Circuit temyiz kararı, portal açılış olasılıkları ve 3 takvim senaryosu).\n"
        "• 🗺️ *360° Yaşam Döngüsü:* `/surec` (İlk başvurudan ABD'de ilk 90 güne kadar 10 aşamalı rehber).\n"
        "• ✈️ *Dosya Taşıma & Dilekçe:* `/dosya_tasima` (Güncel oturum şartı, KCC vs Konsolosluk ve İngilizce resmi dilekçe).\n"
        "• 🏛️ *360° Amerikan Vize Danışmanı:* `/vize_analiz` (DV, EB-2 NIW, O-1, E-2, F-1, B1/B2 214b profil analizi).\n"
        "• 📰 *Günün 2 Haberi & Senaryo Analizi:* `/haber_analiz` ve `/bugun` (Güncel 2 haber üzerine 'bu şekilde olabilir, hazır olmalıyız' yorumu).\n"
        "• 📊 *Hazırlık & Risk Karnesi:* `/karne` (100 üzerinden puanlama ve en acil 3 eylem adımı).\n"
        "• 💵 *Yaşam Maliyeti & Runway:* `/hesapla` (Taşınma masrafları ve birikiminizin kaç ay yeteceği analizi).\n"
        "• 🏙️ *Eyalet Kıyaslama:* `/eyalet` (Texas, California, Florida, Washington, New York vergi ve maaş karşılaştırması).\n"
        "• 🔢 *Case Number & KCC Proaktif Aksiyon:* `/case` (Sıra numarası senaryoları, dar takvim önlemleri ve KCC'ye 'onlara şu şekilde söyleyelim' hazır İngilizce maili).\n"
        "• 🧠 *Benim Yerine Düşün:* `/aksiyon` (Sıra numarası, meslek, bütçe ve DS-260 durumuna göre olası senaryolar ve hazır resmi mailler).\n"
        "• 🚀 *Alternatif Vizeler:* `/vize_rotalari` (Şirketsiz doğrudan Green Card EB-2 NIW ve diğer rotalar).\n"
        "• 🧠 *Derin Sohbet & Profil Hafızası:* Mesleğini, bütçeni, aileni ve önceki konuşmalarımızı hatırlarım (`/profilim`, `/hafiza_temizle`).\n"
        "• 📸 *Fotoğraf & Pasaport Testi:* `/fotograf` (600x600 px, sRGB, arka plan aydınlığı ve JPEG denetimi).\n\n"
        "👇 *Menüden bir işlem seçebilir veya aklına gelen her şeyi doğrudan bir dosta danışır gibi yazabilirsin:*"
    )
    await safe_reply_or_edit(
        update,
        welcome_text,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    profile["chat_history"] = []
    profile["awaiting_ds260_field"] = None
    profile["interview_step"] = None
    save_state(state)
    await update.message.reply_text(
        "🧹 *Sohbet hafızası temizlendi!*\n"
        "Checklist, DS-260 ve profil kayıtlarınız korundu. (Profilinizi sıfırlamak isterseniz: `/profil_temizle`). Yeni bir konu veya soruyla dilediğiniz gibi devam edebiliriz.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_profilim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    view_text = format_profile_view(profile.get("user_facts", {}))
    await update.message.reply_text(
        view_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_profil_temizle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    clear_profile_facts(profile)
    save_state(state)
    await update.message.reply_text(
        "🧹 *Kişisel profil hafızanız temizlendi!*\n"
        "Meslek, bütçe, aile ve lokasyon bilgileriniz sıfırlandı. Yeni mesajlarınızla dilediğiniz zaman otomatik olarak tekrar oluşturabilirsiniz.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_profil(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "ℹ️ *Profil Güncelleme Kullanımı:*\n"
            "`/profil <alan> <bilgi>`\n\n"
            "Örnekler:\n"
            "• `/profil meslek Yazılım Mühendisi`\n"
            "• `/profil butce 20.000$`\n"
            "• `/profil hedef Austin, Texas`\n"
            "• `/profil aile Evli, 1 çocuk`\n"
            "• `/profil egitim Lisans`\n"
            "• `/profil ingilizce B2`\n\n"
            "Mevcut profilinizi görmek için: `/profilim`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    field_alias = args[0]
    val = " ".join(args[1:]).strip()
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    facts = profile.setdefault("user_facts", {})
    canon = set_profile_field(facts, field_alias, val)
    if not canon:
        await update.message.reply_text(
            f"⚠️ Geçersiz profil alanı: `{field_alias}`\n"
            "Kullanılabilir alanlar: `meslek`, `butce`, `hedef`, `aile`, `egitim`, `ingilizce`, `not`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    save_state(state)
    await update.message.reply_text(
        f"✅ Profil güncellendi!\n*{canon}*: {val}\n\nProfilinizi görmek için: `/profilim`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_karne(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    audit = generate_readiness_audit(profile)
    report = format_audit_report(audit)
    await update.message.reply_text(
        report,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_hesapla(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    facts = profile.get("user_facts", {})
    args = context.args or []

    budget_input = args[0] if len(args) >= 1 else facts.get("butce", "20000")
    state_input = args[1] if len(args) >= 2 else facts.get("hedef_lokasyon", "texas")
    is_fam = "evli" in facts.get("medeni_durum", "").lower() or "çocuk" in facts.get("medeni_durum", "").lower()

    calc = calculate_relocation_budget(budget_input, state_input, is_family=is_fam)
    report = format_runway_report(calc)
    await update.message.reply_text(
        report,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_calc_keyboard(),
    )


async def cmd_eyalet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) >= 2:
        text = compare_states(args[0], args[1])
    elif len(args) == 1:
        prof = get_state_profile(args[0])
        if prof:
            text = (
                f"🏙️ *{prof['title']} Detaylı Eyalet Analizi*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏛️ *Gelir Vergisi:* {prof['income_tax']}\n"
                f"🛍️ *Satış Vergisi:* {prof['sales_tax']}\n"
                f"🏠 *Ortalama 1+1 Kira:* {prof['rent_1br']}\n"
                f"💻 *Tech / Yazılım Maaşı:* {prof['tech_salary']}\n"
                f"🩺 *Sağlık / Hemşire Maaşı:* {prof['nurse_salary']}\n"
                f"☀️ *İklim:* {prof['climate']}\n"
                f"🚗 *Araç İhtiyacı:* {prof['car']}\n"
                f"🇹🇷 *Türk Topluluğu:* {prof['turkish_community']}\n\n"
                f"🌟 *Artıları:* {prof['pros']}\n"
                f"⚠️ *Dikkat:* {prof['cons']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 Başka bir eyaletle kıyaslamak için: `/eyalet {args[0]} california`"
            )
        else:
            text = f"'{args[0]}' bulunamadı. Kullanılabilir eyaletler: `texas`, `california`, `florida`, `washington`, `north_carolina`, `new_york`."
    else:
        text = (
            "🏙️ *ABD Eyalet & Şehir Karşılaştırma Rehberi*\n\n"
            "Hangi eyalete yerleşeceğinizi belirlerken vergi, kira, iş imkanları ve Türk nüfusu açısından analiz etmek istediğiniz eyaleti seçin veya doğrudan kıyaslayın:\n\n"
            "• Örnek: `/eyalet texas california` veya `/eyalet washington`"
        )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_states_keyboard(),
    )


async def cmd_case(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    facts = profile.get("user_facts", {})
    args = context.args or []
    case_val = args[0] if args else facts.get("case_number", "")
    if not case_val:
        await safe_reply_or_edit(
            update,
            "🔢 *DV Case Number, Olası Senaryolar & Hazır KCC Maili*\n\n"
            "Case numaranızı girdiğinizde senin yerine olası senaryoları (Normal ilerleme, Ankara yoğunluğu, 30 Eylül dar takvim) kurar, "
            "hemen alacağımız aksiyonları belirler ve *KCC'ye gönderebileceğimiz hazır İngilizce mail taslağını ('Onlara şu şekilde söyleyelim')* üretirim:\n\n"
            "Kullanım: `/case <numara>`\n"
            "Örnek: `/case 2027EU00028500` veya `/case EU28500` veya `/case 2027AS3500`\n\n"
            "*(Bu numara profilinize otomatik kaydedilir ve tüm stratejileriniz buna göre planlanır)*",
            reply_markup=build_case_actions_keyboard(),
        )
        return

    analysis = analyze_case_number(case_val, profile)
    if analysis.get("valid"):
        facts["case_number"] = analysis["raw"]
        save_state(state)

    report = format_case_analysis(analysis, profile)
    await safe_reply_or_edit(
        update,
        report,
        reply_markup=build_case_actions_keyboard(),
    )


async def cmd_aksiyon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Proactive 'Think For Me' command synthesizing scenarios, bottlenecks, and ready-to-send KCC/Embassy emails."""
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    report = build_proactive_action_plan(profile)
    record_chat_turn(profile, "/aksiyon", report)
    save_state(state)
    await safe_reply_or_edit(
        update,
        report,
        reply_markup=build_case_actions_keyboard(),
    )


async def cmd_vize_rotalari(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    text = get_visa_routes_guide(profile)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_sozluk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    query = " ".join(args).strip()
    text = lookup_glossary(query)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_glossary_keyboard(),
    )


async def cmd_mahkeme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    facts = profile.get("user_facts", {})
    report = analyze_court_and_timeline(facts)
    await update.message.reply_text(
        report,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_surec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    guide = get_full_lifecycle_guide()
    await update.message.reply_text(
        guide,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_dosya_tasima(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    scenario = " ".join(context.args or []).strip()
    thinking = None
    if scenario:
        thinking = await update.message.reply_text("✈️ _Dosya taşıma stratejisi ve İngilizce resmi dilekçe hazırlanıyor..._", parse_mode=ParseMode.MARKDOWN)
    ai_fn = _run_coach_gemini_snippet if (scenario and HAS_GENAI and GEMINI_API_KEY) else None
    report = await asyncio.to_thread(
        analyze_transfer_and_build_letter,
        scenario,
        profile,
        use_ai=bool(ai_fn),
        ai_callable=ai_fn,
    )
    if scenario:
        record_chat_turn(profile, f"/dosya_tasima {scenario}", report)
        save_state(state)
    await safe_reply_or_edit(
        update,
        report,
        thinking_msg=thinking,
        reply_markup=build_transfer_keyboard(),
    )


async def cmd_vize_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    report = analyze_all_us_visas(profile)
    await safe_reply_or_edit(
        update,
        report,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_haber_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    thinking = await update.message.reply_text("📰 _Günün en güncel 2 haberi çekilip stratejik senaryo analizi yapılıyor..._", parse_mode=ParseMode.MARKDOWN)
    news = await asyncio.to_thread(fetch_latest_gc_news, 2)
    ai_fn = _run_coach_gemini_snippet if (HAS_GENAI and GEMINI_API_KEY) else None
    report = await asyncio.to_thread(analyze_daily_news_scenarios, news, profile, ai_fn)
    record_chat_turn(profile, "/haber_analiz", report)
    save_state(state)
    await safe_reply_or_edit(
        update,
        report,
        thinking_msg=thinking,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_bugun(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    thinking = await update.message.reply_text("☀️ _Günlük planınız ve günün 2 kritik haberi analiz ediliyor..._", parse_mode=ParseMode.MARKDOWN)
    news = await asyncio.to_thread(fetch_latest_gc_news, 2)
    brief = await asyncio.to_thread(generate_daily_coaching_brief, profile, news, True)
    await safe_reply_or_edit(
        update,
        brief,
        thinking_msg=thinking,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_bildirim_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    await update.message.reply_text(
        generate_daily_coaching_brief(profile),
        disable_web_page_preview=True,
    )


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Chat ID: {update.effective_chat.id}\n"
        "Kalıcı bildirim hedefi için Render Environment bölümünde COACH_CHAT_ID olarak ekleyebilirsiniz."
    )


async def cmd_yorumlar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subject = " ".join(context.args or []).strip()
    if not subject:
        subject = "DV-2027 Red Eagle Law davası hakkında göçmenlik avukatları, Reddit ve forumlarda neler konuşuluyor?"
    sent = await update.message.reply_text("💬 Hukukçu ve forum görüşleri araştırılıyor...")
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    reply = await asyncio.to_thread(answer_user_question, subject, profile, False)
    record_chat_turn(profile, f"/yorumlar {subject}", reply)
    save_state(state)
    await safe_reply_or_edit(update, reply, thinking_msg=sent, reply_markup=build_main_menu_keyboard())


async def cmd_ara(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topic = " ".join(context.args or []).strip()
    if not topic:
        await update.message.reply_text(
            "🔎 Canlı web araştırması için örnek:\n"
            "`/ara DV-2027 başvuru duyuruları` veya `/ara Teksas Austin yazılımcı maaşları`\n\n"
            "Gizliliğiniz için pasaport no veya kişisel verilerinizi sorguya eklemeyiniz.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    status_msg = await update.message.reply_text("🔎 Web kaynakları taranıyor...")
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    answer = await asyncio.to_thread(answer_user_question, topic, profile, True)
    record_chat_turn(profile, f"/ara {topic}", answer)
    save_state(state)
    await safe_reply_or_edit(update, answer, thinking_msg=status_msg, reply_markup=build_main_menu_keyboard())


async def cmd_ai_durum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not HAS_GENAI:
        await update.message.reply_text("🔴 `google-genai` kütüphanesi yüklü değil.")
        return
    if not GEMINI_API_KEY:
        await update.message.reply_text("🔴 GEMINI_API_KEY tanımlı değil.")
        return

    check_message = await update.message.reply_text("🔎 Gemini API bağlantısı test ediliyor...")

    def probe_gemini():
        client = genai.Client(api_key=GEMINI_API_KEY)
        response, selected = generate_with_fallback(
            client=client,
            preferred=GEMINI_MODEL,
            contents="Sadece OK yaz.",
            config=genai_types.GenerateContentConfig(temperature=0),
        )
        return selected if response and response.text and response.text.strip() else None

    try:
        model = await asyncio.to_thread(probe_gemini)
        if model:
            await check_message.edit_text(
                f"🟢 Gemini API bağlantısı doğrulandı.\n"
                f"Aktif Model: `{model}`\n"
                "Sınırsız Kişisel Koçluk ve Çoklu Sohbet Hafızası devrede."
            )
        else:
            await check_message.edit_text("🟠 Gemini erişilebilir fakat model boş yanıt döndürdü.")
    except Exception as exc:
        code = getattr(exc, "code", None)
        await check_message.edit_text(
            f"🔴 Gemini API bağlantı hatası: {type(exc).__name__} (Kod: {code})\n"
            "API anahtarınızı ve Google AI Studio erişiminizi kontrol edin."
        )


async def cmd_durum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("🔍 Resmi kaynaklar ve mahkeme haberleri taranıyor...")
    report = await asyncio.to_thread(format_status_report)
    await safe_reply_or_edit(update, report, thinking_msg=msg, reply_markup=build_main_menu_keyboard())


async def cmd_rehber(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧭 *DV-2027: 5 Fazlı Hızlandırılmış Hazırlık Rehberi*\n\n"
        "İncelemek istediğiniz faza tıklayarak ayrıntılı stratejiyi görebilirsiniz:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_phases_keyboard(),
    )


async def cmd_mulakat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    profile["interview_step"] = 0
    profile["awaiting_ds260_field"] = None
    save_state(state)
    await update.message.reply_text(
        "🎯 *ABD Konsolosluğu Canlı Mülakat Simülasyonu Başladı!*\n\n"
        "Şu andan itibaren ABD Konsolosluğu'ndaki vize memurunuzum. Size 6 kritik soru soracağım ve her cevabınızı analiz edeceğim.\n\n"
        f"🗣️ *İlk Sorum:*\n{INTERVIEW_QUESTIONS[0]}\n\n_(Çıkmak için `/iptal` yazabilirsiniz)_",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_takvim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        format_calendar_report(),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    text, markup = build_checklist_view(profile)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def cmd_ds260(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)
    text, markup = build_ds260_view(profile)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def cmd_fotograf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📸 *Otomatik Fotoğraf ve Pasaport Taraması Doğrulayıcı*\n\n"
        "Dosyalarınızın ABD teknik standartlarına uygunluğunu test etmek için:\n"
        "1️⃣ Telegram'da *Ataş (📎) -> Dosya (Document)* olarak gönderin.\n"
        "2️⃣ *Biyometrik fotoğrafınız* için: *JPEG*, *600 x 600 px* ve *<= 240 KB* kontrolü yaparım.\n"
        "3️⃣ *Pasaport kimlik/imza taramanız* için: PDF değil *JPEG/JFIF* ve *<= 5 MB* kontrolü yaparım.\n\n"
        "🔗 Kafa/göz hizası kırpma aracı: [ABD Dışişleri Photo Tool](https://tsg.phototool.state.gov/photo)"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=build_main_menu_keyboard(),
    )


# ============================================================================
# CALLBACK (BUTON) İŞLEYİCİSİ
# ============================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    state = load_state()
    profile = get_user_profile(state, chat_id)
    data = query.data or ""

    if data == "menu_main":
        await query.edit_message_text(
            "🇺🇸 *Kişisel Koç & 360° Süreç Yöneticisi Ana Menüsü*\nBir modül seçin veya merak ettiğiniz her şeyi doğrudan mesaj olarak yazın:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_status":
        await query.edit_message_text("🔍 Güncel durum ve mahkeme haberleri kontrol ediliyor...")
        report = await asyncio.to_thread(format_status_report)
        await safe_edit_response(query.message, report, reply_markup=build_main_menu_keyboard())
    elif data == "menu_phases":
        await query.edit_message_text(
            "🧭 *DV-2027: 5 Fazlı Hızlandırılmış Hazırlık Rehberi*\nDetaylarını görmek istediğiniz faza tıklayın:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_phases_keyboard(),
        )
    elif data.startswith("phase:"):
        pkey = data.split(":", 1)[1]
        ptext = PHASES_GUIDE.get(pkey, "Faz bilgisi bulunamadı.")
        await query.edit_message_text(
            ptext,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_phases_keyboard(),
        )
    elif data == "menu_opinions":
        await query.edit_message_text("💬 Hukukçu ve forum görüşleri taranıyor...")
        text = "DV-2027 davası konusunda göçmenlik avukatları, Reddit ve forumlarda neler söyleniyor?"
        reply = await asyncio.to_thread(answer_user_question, text, profile, False)
        record_chat_turn(profile, text, reply)
        save_state(state)
        await safe_edit_response(query.message, reply, reply_markup=build_main_menu_keyboard())
    elif data == "menu_websearch":
        await query.edit_message_text(
            "🔎 Canlı web araştırması için mesaja `/ara konu` yazın.\n"
            "Örnek: `/ara DV-2027 kayıt ücreti` veya `/ara Teksas kira fiyatları`\n"
            "Aramada pasaport numarası veya kişisel bilgi paylaşmayınız.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_clearmemory":
        profile["chat_history"] = []
        save_state(state)
        await query.edit_message_text(
            "🧹 *Sohbet hafızası temizlendi!*\nChecklist, DS-260 ve profil kayıtlarınız korundu. Yeni bir soruyla devam edebiliriz.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_profile":
        view_text = format_profile_view(profile.get("user_facts", {}))
        await query.edit_message_text(
            view_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_interview":
        profile["interview_step"] = 0
        profile["awaiting_ds260_field"] = None
        save_state(state)
        await query.edit_message_text(
            "🎯 *ABD Konsolosluğu Canlı Mülakat Simülasyonu Başladı!*\n\n"
            f"🗣️ *İlk Sorum:*\n{INTERVIEW_QUESTIONS[0]}\n\n_(Cevabınızı mesaj olarak yazın, çıkmak için `/iptal` yazın)_",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "menu_calendar":
        await query.edit_message_text(
            format_calendar_report(),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_checklist":
        text, markup = build_checklist_view(profile)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    elif data.startswith("chk_toggle:"):
        key = data.split(":", 1)[1]
        current = profile["checklist"].get(key, False)
        profile["checklist"][key] = not current
        save_state(state)
        text, markup = build_checklist_view(profile)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    elif data == "menu_ds260":
        text, markup = build_ds260_view(profile)
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
    elif data.startswith("ds260_edit:"):
        field_key = data.split(":", 1)[1]
        field_label = dict(DS260_FIELDS).get(field_key, field_key)
        profile["awaiting_ds260_field"] = field_key
        profile["interview_step"] = None
        save_state(state)
        await query.edit_message_text(
            f"✏️ *{field_label}*\n\nLütfen bu alan için bilginizi mesaj olarak yazıp gönderin (İptal etmek için `/iptal` yazabilirsiniz):",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif data == "menu_validator":
        await query.edit_message_text(
            "📸 *Fotoğraf & Pasaport Dosyası Denetleyicisi*\n\n"
            "Lütfen biyometrik fotoğrafınızı veya pasaport taramanızı bu sohbete *Dosya (Document)* olarak gönderin. Format, piksel ve boyut uygunluğunu otomatik denetleyeceğim!\n\n"
            "🔗 Resmi Kırpma Aracı: [Photo Tool](https://tsg.phototool.state.gov/photo)",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_confno":
        profile["awaiting_ds260_field"] = "__CONF_NO__"
        profile["interview_step"] = None
        save_state(state)
        existing = profile.get("confirmation_number", "")
        msg = (
            f"🔐 *Kayıtlı Onay Numaranız (Confirmation Number):* `{existing}`\n\n"
            if existing
            else "🔐 *Henüz kayıtlı bir Confirmation Number yok.*\n\n"
        )
        msg += "Başvurunuzu tamamladıktan sonra aldığınız onay numarasını mesaj olarak yazıp kaydedebilirsiniz (İptal için `/iptal`):"
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_mahkeme":
        facts = profile.get("user_facts", {})
        report = analyze_court_and_timeline(facts)
        await safe_edit_response(query.message, report, reply_markup=build_main_menu_keyboard())
    elif data == "menu_surec":
        guide = get_full_lifecycle_guide()
        await safe_edit_response(query.message, guide, reply_markup=build_main_menu_keyboard())
    elif data == "menu_karne":
        audit = generate_readiness_audit(profile)
        report = format_audit_report(audit)
        await safe_edit_response(query.message, report, reply_markup=build_main_menu_keyboard())
    elif data == "menu_hesapla":
        facts = profile.get("user_facts", {})
        b = facts.get("butce", "20000")
        loc = facts.get("hedef_lokasyon", "texas")
        is_fam = "evli" in facts.get("medeni_durum", "").lower() or "çocuk" in facts.get("medeni_durum", "").lower()
        calc = calculate_relocation_budget(b, loc, is_family=is_fam)
        report = format_runway_report(calc)
        await safe_edit_response(query.message, report, reply_markup=build_calc_keyboard())
    elif data.startswith("calc_quick:"):
        st = data.split(":", 1)[1]
        facts = profile.get("user_facts", {})
        b = facts.get("butce", "20000")
        is_fam = "evli" in facts.get("medeni_durum", "").lower() or "çocuk" in facts.get("medeni_durum", "").lower()
        calc = calculate_relocation_budget(b, st, is_family=is_fam)
        report = format_runway_report(calc)
        await safe_edit_response(query.message, report, reply_markup=build_calc_keyboard())
    elif data == "menu_eyalet":
        text = (
            "🏙️ *ABD Eyalet & Şehir Karşılaştırma Rehberi*\n\n"
            "Detaylı analizini görmek istediğiniz eyaleti seçin veya doğrudan kıyaslayın:\n\n"
            "_(Ayrıca `/eyalet texas california` komutuyla da dilediğiniz iki eyaleti karşılaştırabilirsiniz)_"
        )
        await safe_edit_response(query.message, text, reply_markup=build_states_keyboard())
    elif data.startswith("state_view:"):
        st = data.split(":", 1)[1]
        prof = get_state_profile(st)
        if prof:
            text = (
                f"🏙️ *{prof['title']} Detaylı Eyalet Analizi*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏛️ *Gelir Vergisi:* {prof['income_tax']}\n"
                f"🛍️ *Satış Vergisi:* {prof['sales_tax']}\n"
                f"🏠 *Ortalama 1+1 Kira:* {prof['rent_1br']}\n"
                f"💻 *Tech / Yazılım Maaşı:* {prof['tech_salary']}\n"
                f"🩺 *Sağlık / Hemşire Maaşı:* {prof['nurse_salary']}\n"
                f"☀️ *İklim:* {prof['climate']}\n"
                f"🚗 *Araç İhtiyacı:* {prof['car']}\n"
                f"🇹🇷 *Türk Topluluğu:* {prof['turkish_community']}\n\n"
                f"🌟 *Artıları:* {prof['pros']}\n"
                f"⚠️ *Dikkat:* {prof['cons']}\n"
            )
        else:
            text = "Eyalet bulunamadı."
        buttons = [
            [InlineKeyboardButton("⚖️ California ile Kıyasla", callback_data=f"state_comp:{st}:california")],
            [InlineKeyboardButton("🔙 Eyaletler Listesi", callback_data="menu_eyalet")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="menu_main")],
        ]
        await safe_edit_response(query.message, text, reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("state_comp:"):
        parts = data.split(":")
        s1 = parts[1] if len(parts) > 1 else "texas"
        s2 = parts[2] if len(parts) > 2 else "california"
        text = compare_states(s1, s2)
        buttons = [
            [InlineKeyboardButton("🔙 Eyaletler Listesi", callback_data="menu_eyalet")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="menu_main")],
        ]
        await safe_edit_response(query.message, text, reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "menu_case":
        facts = profile.get("user_facts", {})
        case_val = facts.get("case_number", "")
        if case_val:
            analysis = analyze_case_number(case_val, profile)
            report = format_case_analysis(analysis, profile)
        else:
            report = (
                "🔢 *DV Case Number, Olası Senaryolar & KCC Aksiyon Planı*\n\n"
                "Henüz kayıtlı bir Case Number'ınız yok.\n"
                "Sıra numaranızı girdiğinizde olası senaryoları, dar takvim önlemlerini ve *KCC'ye hemen gönderebileceğimiz hazır İngilizce e-posta taslağını* çıkarırım:\n"
                "`/case 2027EU00028500` veya doğrudan sohbete `Sıra numaram EU28500` yazabilirsiniz.\n\n"
                "Aşağıdaki butonlardan tüm resmi KCC / Konsolosluk mail taslaklarına hemen ulaşabilirsiniz:"
            )
        await safe_edit_response(query.message, report, reply_markup=build_case_actions_keyboard())
    elif data == "menu_aksiyon":
        report = build_proactive_action_plan(profile)
        await safe_edit_response(query.message, report, reply_markup=build_case_actions_keyboard())
    elif data.startswith("case_mail:"):
        mail_kind = data.split(":", 1)[1]
        report = generate_proactive_case_emails(mail_kind, profile)
        await safe_edit_response(query.message, report, reply_markup=build_case_actions_keyboard())
    elif data == "menu_vize_rotalari":
        text = get_visa_routes_guide(profile)
        await safe_edit_response(query.message, text, reply_markup=build_main_menu_keyboard())
    elif data == "menu_sozluk":
        text = lookup_glossary("")
        await safe_edit_response(query.message, text, reply_markup=build_glossary_keyboard())
    elif data.startswith("glossary:"):
        term = data.split(":", 1)[1]
        text = lookup_glossary(term)
        buttons = [
            [InlineKeyboardButton("📖 Tüm Sözlük", callback_data="menu_sozluk")],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
        ]
        await safe_edit_response(query.message, text, reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "ds260_audit":
        await query.edit_message_text("🔍 _DS-260 '3 Göz Kuralı' tutarlılık ve 221(g) risk taraması yapılıyor..._", parse_mode=ParseMode.MARKDOWN)
        ai_fn = _run_coach_gemini_snippet if (HAS_GENAI and GEMINI_API_KEY) else None
        report = await asyncio.to_thread(audit_ds260_consistency, profile, DS260_FIELDS, ai_fn)
        buttons = [
            [InlineKeyboardButton("📝 DS-260 Düzenle", callback_data="menu_ds260")],
            [InlineKeyboardButton("🏠 Ana Menü", callback_data="menu_main")],
        ]
        await safe_edit_response(query.message, report, reply_markup=InlineKeyboardMarkup(buttons))
    elif data == "menu_transfer":
        text = analyze_transfer_and_build_letter("", profile)
        await safe_edit_response(query.message, text, reply_markup=build_transfer_keyboard())
    elif data.startswith("transfer_tmpl:"):
        kind = data.split(":", 1)[1]
        scenario_map = {
            "unlock": "DS-260 formumun kilidini açıp adres ve konsolosluk bilgisini güncellemek istiyorum",
            "transfer": "Hedef ülkede yasal oturum iznim bulunuyor, dosyamı bu konsolosluğa taşımak istiyorum",
            "expedited": "F-1 okul başlangıcı veya acil iş/tıbbi gerekçeyle B1/B2/F-1 acil randevu talep ediyorum",
        }
        sc = scenario_map.get(kind, "Dosya taşıma talebi")
        report = analyze_transfer_and_build_letter(sc, profile)
        await safe_edit_response(query.message, report, reply_markup=build_transfer_keyboard())
    elif data == "menu_vize_analiz":
        report = analyze_all_us_visas(profile)
        await safe_edit_response(query.message, report, reply_markup=build_main_menu_keyboard())
    elif data == "menu_haber_analiz":
        await query.edit_message_text("📰 _Günün 2 güncel haberi çekilip 'bu şekilde olabilir, hazır olmalıyız' senaryosu kuruluyor..._", parse_mode=ParseMode.MARKDOWN)
        news = await asyncio.to_thread(fetch_latest_gc_news, 2)
        ai_fn = _run_coach_gemini_snippet if (HAS_GENAI and GEMINI_API_KEY) else None
        report = await asyncio.to_thread(analyze_daily_news_scenarios, news, profile, ai_fn)
        record_chat_turn(profile, "Günün 2 haberi stratejik yorumu", report)
        save_state(state)
        await safe_edit_response(query.message, report, reply_markup=build_main_menu_keyboard())


# ============================================================================
# DOSYA (FOTOĞRAF VE PASAPORT TARAMASI) DOĞRULAMA İŞLEYİCİSİ
# ============================================================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc: Optional[Document] = update.message.document
    if not doc:
        return

    file_name = (doc.file_name or "dosya").lower()
    file_size_bytes = doc.file_size or 0
    file_size_kb = file_size_bytes / 1024.0

    if file_name.endswith(".pdf") or doc.mime_type == "application/pdf":
        await update.message.reply_text(
            "❌ *HATA: PDF Formatı Kabul Edilmez!*\n\n"
            "ABD Dışişleri Bakanlığı kurallarına göre pasaport taraması ve fotoğraflar *kesinlikle JPEG / JFIF (.jpg / .jpeg)* formatında olmalıdır. PDF dosyaları reddedilir.\n"
            "👉 Lütfen dosyanızı *JPEG* olarak kaydedip tekrar gönderin.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        tg_file = await doc.get_file()
        bio = io.BytesIO()
        await tg_file.download_to_memory(out=bio)
        raw_bytes = bio.getvalue()
        img = Image.open(io.BytesIO(raw_bytes))
        width, height = img.size
    except Exception as exc:
        await update.message.reply_text(
            f"⚠️ Gönderdiğiniz dosya görüntü olarak okunamadı ({exc}). Lütfen `.jpg` / `.jpeg` formatında gönderin."
        )
        return

    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)

    # Kareye yakınsa veya dosya adı foto/photo içeriyorsa biyometrik fotoğraf olarak doğrula
    if width == height or "foto" in file_name or "photo" in file_name or file_size_kb <= 350:
        result = validate_biometric_photo(raw_bytes, file_name)
        if result["valid"]:
            profile["checklist"]["photo_taken"] = True
            profile["checklist"]["photo_tested"] = True
            save_state(state)
        await update.message.reply_text(
            result["formatted_report"],
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    # Pasaport Taraması Doğrulaması
    result = validate_passport_scan(raw_bytes, file_name)
    if result["valid"]:
        profile["checklist"]["passport_scan"] = True
        save_state(state)
    await update.message.reply_text(
        result["formatted_report"],
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def handle_photo_compressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        bio = io.BytesIO()
        await tg_file.download_to_memory(out=bio)
        raw_bytes = bio.getvalue()
        result = validate_biometric_photo(raw_bytes, "compressed_photo.jpg")
        text = (
            "ℹ️ *Önemli İpucu:* Fotoğrafı normal resim olarak gönderdiğiniz için Telegram otomatik sıkıştırdı.\n"
            "Yine de genel oran ve aydınlık ön-analizini gerçekleştirdim:\n\n"
            f"{result['formatted_report']}\n\n"
            "⚠️ *Resmi Kayıt Uyarısı:* DV sistemine yüklerken tam 600x600 piksel ve <=240 KB şarttır. "
            "Kesin piksel kontrolü için lütfen fotoğrafı *Ataş (📎) -> Dosya (Document)* olarak gönderin!"
        )
    except Exception:
        text = (
            "ℹ️ *Önemli İpucu:* Telegram normal fotoğrafları otomatik sıkıştırır.\n\n"
            "Piksel ve dosya boyutunu hatasız test edebilmem için lütfen fotoğrafı *Ataş (📎) -> Dosya (Document)* olarak gönderin!"
        )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ============================================================================
# METİN MESAJLARI (SINIRSIZ KOÇLUK, SOHBET HAFIZASI, MÜLAKAT, DS-260)
# ============================================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return

    state = load_state()
    chat_id = update.effective_chat.id
    profile = get_user_profile(state, chat_id)

    if text.lower() in ("/iptal", "iptal"):
        profile["awaiting_ds260_field"] = None
        profile["interview_step"] = None
        save_state(state)
        await update.message.reply_text(
            "İşlem iptal edildi. Bana istediğiniz soruyu doğrudan sorabilir veya menüden devam edebilirsiniz:",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    # 1. Mülakat Provası Akışı
    step = profile.get("interview_step")
    if step is not None and 0 <= step < len(INTERVIEW_QUESTIONS):
        current_q = INTERVIEW_QUESTIONS[step]
        next_step = step + 1
        next_q = INTERVIEW_QUESTIONS[next_step] if next_step < len(INTERVIEW_QUESTIONS) else None
        if next_q is None:
            profile["interview_step"] = None
            profile["checklist"]["mock_interview"] = True
        else:
            profile["interview_step"] = next_step
        save_state(state)

        wait_msg = await update.message.reply_text("🧐 _Vize memuru cevabınızı değerlendiriyor..._", parse_mode=ParseMode.MARKDOWN)
        eval_text = await asyncio.to_thread(evaluate_interview_answer, current_q, text, next_q)
        await safe_reply_or_edit(
            update,
            eval_text,
            thinking_msg=wait_msg,
            reply_markup=build_main_menu_keyboard() if next_q is None else None,
        )
        return

    # 2. Confirmation Number veya DS-260 Alanı Kaydı
    awaiting = profile.get("awaiting_ds260_field")
    if awaiting == "__CONF_NO__":
        profile["confirmation_number"] = text
        profile["checklist"]["ds5501_submitted"] = True
        profile["awaiting_ds260_field"] = None
        save_state(state)
        await update.message.reply_text(
            f"🔐 *Confirmation Number Başarıyla Kaydedildi!* (`{text}`)\n"
            "Resmi sonuç açıklandığında bu numarayla sorgulama yapabilirsiniz.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
        return

    if awaiting:
        profile["ds260"][awaiting] = text
        profile["awaiting_ds260_field"] = None
        save_state(state)
        view_text, markup = build_ds260_view(profile)
        await update.message.reply_text(
            f"✅ *Bilginiz kaydedildi!*\n\n{view_text}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup,
        )
        return

    # 3. Kısıtlamasız Kişisel Koçluk (Çoklu Sohbet & Profil Hafızalı)
    # Kullanıcı mesajından sessiz profil çıkarımı
    extracted = extract_profile_facts(text)
    if extracted:
        user_facts = profile.setdefault("user_facts", {})
        if update_user_facts(user_facts, extracted):
            logger.info("Kullanıcı profili güncellendi: %s", extracted)
            save_state(state)

    thinking_msg = await update.message.reply_text("🧠 _Kişisel koçunuz düşünüyor..._", parse_mode=ParseMode.MARKDOWN)
    reply = await asyncio.to_thread(answer_user_question, text, profile)

    record_chat_turn(profile, text, reply)
    save_state(state)

    use_case_kb = bool(extracted.get("case_number")) or is_case_or_kcc_action_query(text, profile)
    await safe_reply_or_edit(
        update,
        reply,
        thinking_msg=thinking_msg,
        reply_markup=build_case_actions_keyboard() if use_case_kb else build_main_menu_keyboard(),
    )


# ============================================================================
# ARKA PLAN PERİYODİK BİLDİRİM & GÜNLÜK KOÇLUK GÖREVİ
# ============================================================================

async def run_monitoring_cycle(bot) -> None:
    from coach_core import due, new_headlines
    state = load_state()
    subs = list(state.get("subscribers", []))
    override = os.getenv("COACH_CHAT_ID", "").strip()
    if override:
        try:
            n = int(override)
            if n not in subs:
                subs.append(n)
        except ValueError:
            logger.warning("COACH_CHAT_ID sayısal değil.")

    if not subs:
        return

    news = await asyncio.to_thread(fetch_latest_gc_news, 5)
    seen = list(state.get("seen_news_hashes", []))
    changes = new_headlines(news, seen)
    for item in news:
        if item["id"] not in seen:
            seen.append(item["id"])
    state["seen_news_hashes"] = seen[-100:]

    now = datetime.now(TZ_TR)
    day = now.strftime("%Y-%m-%d")

    for chat_id in subs:
        try:
            profile = get_user_profile(state, chat_id)
            if changes:
                ai_fn = _run_coach_gemini_snippet if (HAS_GENAI and GEMINI_API_KEY) else None
                analysis_msg = await asyncio.to_thread(
                    analyze_daily_news_scenarios,
                    changes[:2],
                    profile,
                    ai_fn,
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=analysis_msg[:3900],
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            if due(profile, day, now.hour):
                daily_msg = await asyncio.to_thread(
                    generate_daily_coaching_brief,
                    profile,
                    news[:2],
                    True,
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=daily_msg,
                    disable_web_page_preview=True,
                )
                profile["last_daily_digest"] = day
                save_state(state)
        except Exception as exc:
            logger.warning("Bildirim gönderilemedi: chat=%s hata=%s", chat_id, type(exc).__name__)
    save_state(state)


async def periodic_monitor_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_monitoring_cycle(context.bot)


async def on_bot_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    err_info = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "error_type": type(err).__name__,
        "error_message": str(err),
        "update_id": getattr(update, "update_id", None) if isinstance(update, Update) else None,
    }
    setattr(context.application, "_last_handler_error", err_info)
    if isinstance(err, Conflict):
        logger.warning("Telegram 409 Conflict: Başka bir polling veya webhook aktif.")
    else:
        logger.error("Telegram işleyici hatası: %s - %s", type(err).__name__, err, exc_info=True)
        if isinstance(update, Update) and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ Bir işlem hatası oluştu. /start ile yeniden deneyebilirsiniz."
                )
            except Exception as send_err:
                logger.warning("Hata bildirim mesajı iletilemedi: %s", send_err)


# ============================================================================
# ANA ÇALIŞTIRICI (BULUT WEBHOOK VEYA YEREL POLLING)
# ============================================================================

async def post_init(application: Application) -> None:
    """Register rich command menu in Telegram UI."""
    try:
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Ana menü ve botu başlat"),
            BotCommand("aksiyon", "Benim Yerine Düşün: Senaryo & KCC Aksiyon Planı"),
            BotCommand("case", "Case Number Senaryoları & Hazır KCC Maili"),
            BotCommand("haber_analiz", "Günün 2 Haberi: Senaryo & Hazırlık Yorumu"),
            BotCommand("dosya_tasima", "Dosya Taşıma Stratejisi & İngilizce Dilekçe"),
            BotCommand("vize_analiz", "360° Amerikan Vizesi Uygunluk Analizi"),
            BotCommand("mahkeme", "Mahkeme Durumu, Temyiz & Takvim Analizi"),
            BotCommand("surec", "360° A'dan Z'ye Green Card Yaşam Döngüsü"),
            BotCommand("bugun", "Günlük kişisel adımlar ve 2 haber yorumu"),
            BotCommand("karne", "360° Hazırlık & DS-260 Risk Karnesi (Puan)"),
            BotCommand("hesapla", "Taşınma Maliyeti & Runway Hesaplayıcı"),
            BotCommand("eyalet", "ABD Eyalet & Şehir Kıyaslama Rehberi"),
            BotCommand("vize_rotalari", "Alternatif Vizeler ve B Planı (EB-2 NIW)"),
            BotCommand("sozluk", "Green Card & Göçmenlik Terimleri"),
            BotCommand("mulakat", "Canlı Konsolosluk Mülakat Provası"),
            BotCommand("fotograf", "Biyometrik Fotoğraf & Pasaport Testi"),
            BotCommand("profilim", "Kişisel Profil Hafızanızı Görüntüleyin"),
            BotCommand("profil", "Manuel Profil Bilgisi Güncelleyin"),
            BotCommand("checklist", "12 Adımlı Hızlandırılmış Kontrol Listesi"),
            BotCommand("ds260", "DS-5501 & DS-260 Simülatörü + 3 Göz Denetimi"),
            BotCommand("yorumlar", "Avukat, Reddit ve Forum Analizleri"),
            BotCommand("ara", "Canlı Web Araştırması"),
            BotCommand("durum", "Resmî Kaynaklar ve Mahkeme Raporu"),
            BotCommand("rehber", "5 Fazlı Hızlandırılmış Hazırlık Rehberi"),
            BotCommand("hafiza_temizle", "Sohbet Hafızasını Temizle"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Telegram komut listesi başarıyla kaydedildi.")
    except Exception as exc:
        logger.warning("Telegram komut menüsü kaydedilemedi: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unrestricted Personal Coach & Green Card Manager")
    parser.add_argument(
        "--cron-once",
        action="store_true",
        help="Tek seferlik tarama yapıp çıkar.",
    )
    args = parser.parse_args()

    if not BOT_TOKEN or BOT_TOKEN == "BURAYA_TELEGRAM_BOT_TOKEN_YAZIN":
        raise RuntimeError("TELEGRAM_BOT_TOKEN eksik. Lütfen ortam değişkenini tanımlayın.")

    logger.info("Bot başlatılıyor: Gemini SDK=%s, API Anahtarı=%s", HAS_GENAI, bool(GEMINI_API_KEY))
    app: Application = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    if args.cron_once:
        asyncio.run(run_monitoring_cycle(app.bot))
        logger.info("Tek seferlik cron taraması tamamlandı.")
        return

    # Komut Kayıtları
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("aksiyon", cmd_aksiyon))
    app.add_handler(CommandHandler("strateji", cmd_aksiyon))
    app.add_handler(CommandHandler("haber_analiz", cmd_haber_analiz))
    app.add_handler(CommandHandler("dosya_tasima", cmd_dosya_tasima))
    app.add_handler(CommandHandler("vize_analiz", cmd_vize_analiz))
    app.add_handler(CommandHandler("mahkeme", cmd_mahkeme))
    app.add_handler(CommandHandler("surec", cmd_surec))
    app.add_handler(CommandHandler("hafiza_temizle", cmd_clear_memory))
    app.add_handler(CommandHandler("profilim", cmd_profilim))
    app.add_handler(CommandHandler("profil", cmd_profil))
    app.add_handler(CommandHandler("profil_temizle", cmd_profil_temizle))
    app.add_handler(CommandHandler("karne", cmd_karne))
    app.add_handler(CommandHandler("hesapla", cmd_hesapla))
    app.add_handler(CommandHandler("eyalet", cmd_eyalet))
    app.add_handler(CommandHandler("case", cmd_case))
    app.add_handler(CommandHandler("vize_rotalari", cmd_vize_rotalari))
    app.add_handler(CommandHandler("sozluk", cmd_sozluk))
    app.add_handler(CommandHandler("bugun", cmd_bugun))
    app.add_handler(CommandHandler("bildirim_test", cmd_bildirim_test))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("ara", cmd_ara))
    app.add_handler(CommandHandler("yorumlar", cmd_yorumlar))
    app.add_handler(CommandHandler("ai_durum", cmd_ai_durum))
    app.add_handler(CommandHandler("durum", cmd_durum))
    app.add_handler(CommandHandler("rehber", cmd_rehber))
    app.add_handler(CommandHandler("mulakat", cmd_mulakat))
    app.add_handler(CommandHandler("takvim", cmd_takvim))
    app.add_handler(CommandHandler("checklist", cmd_checklist))
    app.add_handler(CommandHandler("ds260", cmd_ds260))
    app.add_handler(CommandHandler("fotograf", cmd_fotograf))

    # Buton ve Mesaj İşleyicileri
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_compressed))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_error_handler(on_bot_error)

    if app.job_queue:
        app.job_queue.run_repeating(
            periodic_monitor_job,
            interval=CHECK_INTERVAL_SECONDS,
            first=30,
        )

    # Render ortamında (RENDER_EXTERNAL_URL veya WEBHOOK_BASE_URL tanımlıysa) Webhook modunu kullan
    external_url = (os.getenv("WEBHOOK_BASE_URL", "").strip() or os.getenv("RENDER_EXTERNAL_URL", "").strip())
    if external_url:
        from render_runtime import run_render_webhook
        logger.info("Render Webhook modu aktif ediliyor: URL=%s Port=%s", external_url, PORT)
        run_render_webhook(app, bot_token=BOT_TOKEN, port=PORT)
    else:
        # Yerel veya webhooksuz ortamlarda dahili health server + polling
        logger.info("Dış HTTPS webhook URL bulunamadı; yerel modda polling + health server başlatılıyor...")
        start_health_server()
        app.run_polling()


if __name__ == "__main__":
    main()
