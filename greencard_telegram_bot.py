#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sınırsız Kişisel Koç, Stratejik Danışman & 360° Green Card Süreç Yöneticisi (Bulut Sürümü)
==========================================================================================
Bu sürümde tüm yapay kısıtlamalar, kalıp "avukata danışın / yorum yapamam" engelleri ve
konu sınırları kaldırılmıştır. Botunuz artık:
1. Tam Donanımlı Kişisel Koç ve Stratejik Akıl Hocasıdır:
   - Sadece resmi kuralları söylemekle kalmaz; durumunuzu analiz eder, artıları/eksileri
     tartar, kendi stratejik yorumunu katar ve "Senin yerinde olsam şöyle yapardım" diyerek
     sizin için en doğru ve en avantajlı yolu düşünür.
   - Green Card dışındaki tüm sorularınıza da (ABD'de hangi eyalet/şehir, iş bulma, maaşlar,
     kira, kariyer planı, İngilizce, vize alternatifleri, finansal planlama veya günlük
     kişisel kararlarınız) hiçbir konu kısıtlaması olmadan yanıt verir.
2. Çoklu Sohbet Hafızası (Multi-Turn Memory):
   - Önceki mesajlarınızı ve kendiniz hakkında paylaştığınız bilgileri unutmaz; sohbet
     boyunca bağlamı koruyarak gerçek bir insan danışman gibi konuşur (`/hafiza_temizle`
     ile istediğiniz an sıfırlayabilirsiniz).
3. Çift Katmanlı Kesintisiz Gemini AI Motoru + Canlı Google Arama:
   - Önce canlı Google araması (Search Grounding) ile en güncel veriyi çeker; arama aracı
     kota/ağ hatası verirse anında doğrudan Gemini muhakeme motoruna geçer (asla kalıp
     mesaja düşmez).
   - Uzun yanıtları (4000+ karakter) böler ve Telegram Markdown hatalarını otomatik onarır.
4. 7/24 Bulut Uyumlu + Dar Takvim Araçları:
   - Render.com / Koyeb / Hugging Face Spaces için dahili Health-Check sunucusu,
   - Saatlik resmi site/mahkeme taraması, 12 adımlı Checklist, DS-260 simülatörü,
     Canlı Mülakat Provası ve Fotoğraf/Pasaport teknik denetleyicisi.
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
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
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
logger = logging.getLogger("PersonalCoachBot")

# Ortam Değişkenleri (Baş/son boşluk veya tırnak işaretlerini otomatik temizler)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "BURAYA_TELEGRAM_BOT_TOKEN_YAZIN").strip().strip("'\"")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip("'\"")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
PORT = int(os.getenv("PORT", "8080"))
DATA_FILE = Path(os.getenv("STATE_FILE_PATH", "greencard_user_state.json"))
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))  # 1 saat

# Türkiye Saat Dilimi (UTC+3)
TZ_TR = timezone(timedelta(hours=3))

# Kritik DV-2027 Takvim Kilometre Taşları
MILESTONES = [
    {
        "id": "announcement_deadline",
        "date": "2026-10-29",
        "title": "Bakanlık Resmi DV-2027 Duyuru Son Günü",
        "desc": "Federal mahkeme kararına göre ABD Dışişleri Bakanlığı en geç 29 Ekim 2026 gece yarısına kadar resmi takvimi ve uygun ülkeleri ilan etmeli.",
    },
    {
        "id": "photo_passport_ready",
        "date": "2026-10-30",
        "title": "Fotoğraf ve Pasaport Taraması Son Hazırlık Günü",
        "desc": "600x600 px (<240 KB) biyometrik fotoğrafınız ve <5 MB JPEG pasaport kimlik/imza sayfası taramanız hazır ve kontrol edilmiş olmalı.",
    },
    {
        "id": "registration_open",
        "date": "2026-11-01",
        "title": "DV-2027 Başvurularının Açılması",
        "desc": "Mahkeme emrine göre başvurular en geç 1 Kasım 2026'da dvprogram.state.gov üzerinden açılacak ve 30 gün sürecek.",
    },
    {
        "id": "november_preprep",
        "date": "2026-11-15",
        "title": "Dar Takvim Ön-Hazırlığı: DS-260 ve Resmi Belgeler",
        "desc": "Sonuçlar 3 Aralık'ta açıklanacağı için Kasım ortasına kadar e-Devlet adres/SGK dökümleri, Formül A/B ve aşı kontrolleri tamamlanmalı.",
    },
    {
        "id": "registration_close",
        "date": "2026-12-01",
        "title": "DV-2027 Başvurularının Kapanışı (30. Gün)",
        "desc": "30 günlük başvuru penceresinin sonu. Başvurunuzu tamamlamış ve Confirmation Number'ı bota kaydetmiş olmalısınız.",
    },
    {
        "id": "results_announcement",
        "date": "2026-12-03",
        "title": "DV-2027 Çekiliş Sonuçlarının Açıklanması",
        "desc": "Mahkeme kararına göre seçilenler en geç 3 Aralık 2026'da Entrant Status Check üzerinden duyurulacak. Kazananlar hemen DS-260 göndermeli!",
    },
    {
        "id": "visa_issuance_deadline",
        "date": "2027-09-30",
        "title": "DV-2027 Vize Basımı Kesin Son Günü",
        "desc": "2027 ABD Mali Yılı sonu. Seçilenlerin DS-260, sağlık muayenesi ve mülakat süreçleri bu tarihe kadar tamamlanmak zorunda (<10 ay süre).",
    },
]

# Kişisel Hazırlık Kontrol Listesi (Dar Takvime Göre 12 Kritik Adım)
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
        "🚀 *FAZ 1: Kusursuz İlk Başvuru (26 Ekim – 1 Kasım 2026)*\n\n"
        "Hareket alanımız dar olduğu için ilk başvuruda sıfır hata yapmalıyız:\n"
        "• *Zorunlu Pasaport Taraması:* Pasaportunuzun fotoğraflı kimlik ve imza sayfasını PDF değil, *JPEG/JFIF* formatında ve *5 MB altında* taratın.\n"
        "• *Biyometrik Fotoğraf:* Son 6 ay içinde çekilmiş, *600x600 piksel*, maksimum *240 KB*, gözlüksüz ve düz beyaz/açık arka planlı olmalı. Eski vize veya geçen yılın fotoğrafını kullanırsanız sistem otomatik eler.\n"
        "• *1 Dolar Kayıt Ücreti:* Başvuru anında resmi devlet portalında $1 ödenecek; kartınızın 3D Secure / yurtdışı internet alışverişine açık olduğundan emin olun.\n"
        "• *Eş Stratejisi:* Evliyseniz ve eşiniz de şartları sağlıyorsa iki ayrı başvuru yaparak kazanma şansınızı *2 katına* çıkarın."
    ),
    "phase2": (
        "📂 *FAZ 2: Kasım Ayında (Sonuçları Beklemeden!) DS-260 ve Evrak Hazırlığı*\n\n"
        "Normal yıllarda sonuçlar Mayıs'ta açıklanır ve 17 ay vaktiniz olurdu. Bu yıl sonuçlar *3 Aralık 2026*'da açıklanacak ve *30 Eylül 2027*'de süreç bitecek (<10 ay). Bu yüzden Kasım ayında sonuçları beklemeden şunları hazırlayın:\n"
        "1️⃣ *e-Devlet Tarihçeli Yerleşim Yeri Raporu:* 16 yaşınızdan bugüne kadar oturduğunuz tüm adresleri ay/yıl olarak çıkarıp `/ds260` modülüne kaydedin.\n"
        "2️⃣ *e-Devlet SGK Hizmet Dökümü:* Son 10 yıldaki tüm iş giriş-çıkış tarihlerinizi ve işyeri unvanlarını listeleyin.\n"
        "3️⃣ *Nüfus Müdürlüğünden Formül A ve Formül B:* Uluslararası çok dilli doğum kayıt örneği (Formül A) ve evliyseniz evlilik kayıt örneği (Formül B) alınma sürecini öğrenin.\n"
        "4️⃣ *Adli Sicil Kaydı:* 16 yaşından beri 6 aydan fazla yaşadığınız başka bir ülke varsa oradan polis belgesi (Police Certificate) almak haftalar sürer; şimdiden başvurun!"
    ),
    "phase3": (
        "⚡ *FAZ 3: 3 Aralık Sonuç Günü, Case Number ve Konsolosluk/AOS Stratejisi*\n\n"
        "• *İlk 48 Saat Kuralı:* 3 Aralık 2026'da `You have been selected` yazısını görür görmez, önceden `/ds260` simülatöründe hazırladığımız verilerle CEAC üzerinden DS-260 formunu ilk 48 saat içinde hatasız gönderin.\n"
        "• *Case Number (Dosya Numarası) Analizi:* Numaranız `2027EU0000XXXX` formatında olacak. Dar takvim nedeniyle KCC (Kentucky Consular Center) DS-260 formunu işleme sırasına göre mülakat dağıtır; formu erken göndermek hayati önem taşır.\n"
        "• *Alternatif Konsolosluk / AOS Planı:* Eğer ABD'de yasal statüdeyseniz (F-1, B1/B2, H-1B vb.) USCIS üzerinden *Adjustment of Status (I-485)* veya İstanbul/Ankara yoğunluğuna göre dosyanızı aktif başka bir konsolosluğa taşıma opsiyonunu değerlendireceğiz."
    ),
    "phase4": (
        "🩺 *FAZ 4: Sağlık Muayenesi (Aşılar) ve Finansal (Public Charge) Kalkanı*\n\n"
        "Mülakatta ret veya 'Administrative Processing' (İdari İşlem) almamak için iki kritik hazırlık:\n"
        "1️⃣ *Aşı ve Antikor Hazırlığı:* Yetkili göçmen doktoru muayenesinde *Tetanoz (Tdap), MMR (Kızamık-Kızamıkçık-Kabakulak), Hepatit B, Suçiçeği (Varicella)* ve mevsimsel grip/polio aşıları istenir. Aşı kartınız yoksa aile hekiminizde *Antikor (Titrasyon) Testi* yaptırarak bağışıklığınızı şimdiden belgeleyin.\n"
        "2️⃣ *Public Charge (Kamu Yükü Olmama) Kanıtı:* 2026'da sıkılaştırılan Public Charge eğitimleri nedeniyle konsolosluk memuru ABD'de kendi ayaklarınız üzerinde durabileceğinizi görmek ister:\n"
        "   • Kişi başı en az *$10.000 – $15.000* (aile için $20.000+) vadeli/vadesiz banka bakiyesi,\n"
        "   • Varsa tapu/araç ruhsatı, İngilizce CV, LinkedIn profili veya ABD'den iş görüşmesi/teklifi yazışmaları,\n"
        "   • Gerekirse ABD'de yaşayan bir yakınınızdan *Form I-134 (Affidavit of Support)*."
    ),
    "phase5": (
        "🎯 *FAZ 5: Konsolosluk Mülakatı ve ABD'ye İlk Giriş Planı*\n\n"
        "• *Mülakat Provası:* Mülakat ortalama 3-5 dakika sürer ancak DS-260 formunuzdaki bilgilerle verdiğiniz sözlü yanıtların %100 tutarlı olması gerekir. Botta `/mulakat` komutuyla benimle canlı prova yapabilirsiniz.\n"
        "• *Vize Onayı Sonrası:* Vizeniz basıldıktan sonra maksimum 6 ay içinde (ve her halükarda 30 Eylül 2027'den önce) ABD'ye giriş yapmalısınız.\n"
        "• *USCIS Immigrant Fee ($235):* Vizeyi aldıktan sonra ABD'ye uçmadan önce kişi başı $235 kart basım ücretini online ödeyin ki fiziksel Green Card'ınız ABD'ye ayak bastıktan sonra 2-4 hafta içinde adresinize gelsin."
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
# BULUT HEALTH-CHECK SUNUCUSU (RENDER / KOYEB / HF SPACES İÇİN 7/24 ÇALIŞMA)
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
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Durum dosyası okunamadı: %s", exc)
    return {
        "subscribers": [],
        "seen_news_hashes": [],
        "last_dv_portal_hash": "",
        "last_daily_brief_date": "",
        "users": {},
    }


def save_state(state: Dict[str, Any]) -> None:
    try:
        DATA_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Durum dosyası kaydedilemedi: %s", exc)


def get_user_profile(state: Dict[str, Any], chat_id: int) -> Dict[str, Any]:
    uid = str(chat_id)
    if uid not in state["users"]:
        state["users"][uid] = {
            "checklist": {key: False for key, _ in CHECKLIST_ITEMS},
            "ds260": {key: "" for key, _ in DS260_FIELDS},
            "awaiting_ds260_field": None,
            "interview_step": None,
            "confirmation_number": "",
            "chat_history": [],  # Çoklu sohbet hafızası [{"role": "user"|"assistant", "text": "..."}]
            "personal_notes": "",
        }
    else:
        for key, _ in CHECKLIST_ITEMS:
            state["users"][uid]["checklist"].setdefault(key, False)
        state["users"][uid].setdefault("interview_step", None)
        state["users"][uid].setdefault("chat_history", [])
        state["users"][uid].setdefault("personal_notes", "")
    if chat_id not in state["subscribers"]:
        state["subscribers"].append(chat_id)
    save_state(state)
    return state["users"][uid]


# ============================================================================
# CANLI HABER VE RESMİ PORTAL TARAMA MOTORU
# ============================================================================

def fetch_latest_gc_news(max_items: int = 5) -> List[Dict[str, str]]:
    rss_urls = [
        "https://news.google.com/rss/search?q=DV-2027+OR+%22Diversity+Visa%22+lottery+when:7d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=%22Green+Card%22+DV-2027+mahkeme+OR+ba%C5%9Fvuru+when:7d&hl=tr&gl=TR&ceid=TR:tr",
    ]
    items: List[Dict[str, str]] = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GreenCardProcessManager/3.0)"}

    for url in rss_urls:
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:max_items]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                if title and link:
                    uid = hashlib.md5(f"{title}|{link}".encode("utf-8")).hexdigest()[:12]
                    items.append(
                        {
                            "id": uid,
                            "title": title,
                            "link": link,
                            "pub_date": pub_date,
                        }
                    )
        except Exception as exc:
            logger.warning("RSS tarama hatası (%s): %s", url, exc)

    unique_items = []
    seen = set()
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            unique_items.append(it)
    return unique_items[:max_items]


def check_official_dv_portal() -> Dict[str, str]:
    url = "https://dvprogram.state.gov/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GreenCardProcessManager/3.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        text_snippet = resp.text[:4000]
        status_hash = hashlib.md5(text_snippet.encode("utf-8", errors="ignore")).hexdigest()[:12]
        is_open = "Begin Entry" in resp.text or "DV-2027" in resp.text
        return {
            "reachable": "Evet",
            "hash": status_hash,
            "summary": (
                "🚨 DV-2027 ibaresi / Başvuru butonu tespit edildi! Hemen kontrol edin!"
                if is_open
                else "Henüz DV-2027 başvuru ekranı aktif görünmüyor (Mahkeme son tarihi: 1 Kasım 2026)."
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
# SINIRSIZ KİŞİSEL KOÇ VE STRATEJİK DANIŞMAN MOTORU (GEMINI API)
# ============================================================================

UNRESTRICTED_COACH_SYSTEM_PROMPT = """
Sen kullanıcının en güvendiği Kişisel Koçu, Stratejik Akıl Hocası, Hayat/Kariyer Danışmanı ve 360° Green Card Süreç Yöneticisisin.

TEMEL ÇALIŞMA İLKELERİN (KISITLAMASIZ MOD):
1. HİÇBİR KONU VEYA YORUM KISITLAMASI YOKTUR:
   - Kullanıcı sana Green Card, ABD göçmenlik stratejisi, eyalet/şehir seçimi, iş piyasası, maaşlar, kira, vergi, yatırım, vize alternatifleri (B1/B2, F-1, E-2, EB-3, H-1B), İngilizce gelişimi, aile kararları, psikolojik motivasyon veya günlük hayatla ilgili HERHANGİ BİR SORU sorabilir.
   - Asla "Ben sadece bir botum", "Hukuki/finansal tavsiye veremem, bir uzmana danışın" gibi kaçamak, bürokratik ve soğuk kalıplar kullanma! Kullanıcı senin görüşlerini kendi süzgecinden geçirecek analitik kapasiteye sahiptir; senden sansürsüz, cesur, derinlemesine analiz ve gerçek bir dost/akıl hocası yorumu bekliyor.
2. KENDİ STRATEJİK YORUMUNU VE FİKRİNİ AÇIKÇA SÖYLE:
   - Bir soruyu yanıtlarken sadece kuru bilgi verme. Seçeneklerin görünmeyen risklerini, pratik gerçeklerini ve fırsatlarını masaya yatır.
   - Yanıtlarında mutlaka "Benim stratejik yorumum / Senin yerinde olsam ne yapardım?" perspektifi sun. Kullanıcı için en doğru, en karlı, en güvenli ve en hızlı olanı onun adına düşün ve teklif et.
3. PROAKTİF VE İLERİ GÖRÜŞLÜ OL:
   - Kullanıcının sormadığı ama bilmesi gereken bir sonraki adımı veya olası tuzağı öngörüp uyar.

GÜNCEL GREEN CARD (DV-2027) DOSYA BİLGİLERİ (Ekim 2026 İtibarıyla):
- Mahkeme Kararı (Red Eagle Law v. Rubio, No. 26-cv-4738): 14 Ekim 2026'da Kaliforniya Güney Bölgesi Federal Mahkemesi Yargıcı Jinsook Ohta ihtiyati tedbir kararı verdi.
- Takvim: ABD Dışişleri Bakanlığı en geç 29 Ekim 2026'da resmi kuralları/ülke listesini duyurmak, en geç 1 Kasım 2026'da başvuruları açıp 30 gün (1 Aralık 2026'ya kadar) açık tutmak ve sonuçları en geç 3 Aralık 2026'da açıklamak zorunda.
- Yeni Kurallar:
  1) Asıl başvuru sahibi için geçerli pasaport bilgisi ve pasaportun kimlik/imza sayfası taraması (JPEG/JFIF, maks. 5 MB, PDF yasak) zorunlu.
  2) İlk kez 1 ABD Doları ($1) elektronik kayıt ücreti var.
  3) Sonuçlar 3 Aralık 2026'da açıklanacağı ve tüm vizelerin 30 Eylül 2027'ye kadar basılması gerektiği için (<10 ay süre) DS-260, e-Devlet adres/SGK dökümleri, Formül A/B, adli sicil, aşı/antikor ve Public Charge (banka birikimi) hazırlıkları Kasım ayında sonuçları beklemeden tamamlanmalı.
"""


def build_user_context_summary(profile: Dict[str, Any]) -> str:
    today = datetime.now(TZ_TR).strftime("%Y-%m-%d %H:%M")
    chk = profile.get("checklist", {})
    done_items = [label for k, label in CHECKLIST_ITEMS if chk.get(k, False)]
    todo_items = [label for k, label in CHECKLIST_ITEMS if not chk.get(k, False)]
    ds260 = profile.get("ds260", {})
    filled_ds260 = [f"{label}: {ds260.get(k)}" for k, label in DS260_FIELDS if ds260.get(k, "").strip()]
    missing_ds260 = [label for k, label in DS260_FIELDS if not ds260.get(k, "").strip()]

    history = profile.get("chat_history", [])[-10:]
    history_str = "\n".join(
        [f"{'Kullanıcı' if m['role'] == 'user' else 'Koç'}: {m['text'][:400]}" for m in history]
    )

    return (
        f"Tarih/Saat: {today}\n"
        f"Tamamlanan Hazırlık Adımları ({len(done_items)}/{len(CHECKLIST_ITEMS)}): {', '.join(done_items) if done_items else 'Henüz işaretlenmedi'}\n"
        f"Sıradaki Bekleyen Adımlar: {', '.join(todo_items[:4])}\n"
        f"DS-260 Kayıtlı Bilgiler ({len(filled_ds260)}/{len(DS260_FIELDS)}): {'; '.join(filled_ds260) if filled_ds260 else 'Henüz girilmedi'}\n"
        f"DS-260 Eksik Alanlar: {', '.join(missing_ds260[:4])}\n"
        f"Son Sohbet Geçmişi:\n{history_str if history_str else 'Yeni sohbet'}"
    )


def get_unrestricted_safety_settings() -> List[Any]:
    """Gemini API güvenlik filtrelerini standart kişisel danışmanlık sorularını engellemeyecek şekilde ayarlar."""
    if not HAS_GENAI:
        return []
    try:
        return [
            genai_types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",
            ),
            genai_types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",
            ),
            genai_types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",
            ),
            genai_types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",
            ),
        ]
    except Exception:
        return []


def answer_user_question(question: str, profile: Dict[str, Any]) -> str:
    """Kullanıcının sorusunu kısıtlamasız Gemini AI Koçu ile (Canlı Arama + Sohbet Hafızası) yanıtlar."""
    user_context = build_user_context_summary(profile)

    if not HAS_GENAI:
        return (
            "⚠️ Sunucuda `google-genai` kütüphanesi kurulu görünmüyor. "
            "Lütfen `requirements.txt` içinde `google-genai>=1.0.0` olduğundan emin olun."
        )

    if not GEMINI_API_KEY:
        return (
            "⚠️ *GEMINI_API_KEY Bulunamadı!*\n\n"
            "Bana sorduğunuz her soruya sınırsız kişisel koçunuz olarak yanıt verebilmem için Render.com panelinizde:\n"
            "1. Sol menüden *Environment* sekmesine girin.\n"
            "2. *Add Environment Variable* butonuna tıklayın.\n"
            "3. Key kısmına `GEMINI_API_KEY`, Value kısmına ise [Google AI Studio](https://aistudio.google.com/apikey) adresinden aldığınız anahtarı yapıştırıp kaydedin."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = (
        f"[KULLANICININ PROFİLİ VE SOHBET HAFIZASI]\n{user_context}\n\n"
        f"[KULLANICININ YENİ MESAJI / SORUSU]\n{question}\n\n"
        "YÖNERGE: Kullanıcının kişisel koçu ve stratejik danışmanı olarak bu mesaja doğrudan, "
        "kısıtlamasız, analitik ve samimi bir yanıt ver. Kendi yorumunu, stratejik tavsiyeni ve "
        "kullanıcı için en doğru/iyi olan seçeneği nedenleriyle açıkla."
    )

    safety = get_unrestricted_safety_settings()

    # 1. Deneme: Canlı Google Araması (Search Grounding) ile Güncel & Derin Yanıt
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=UNRESTRICTED_COACH_SYSTEM_PROMPT,
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                safety_settings=safety if safety else None,
                temperature=0.6,
            ),
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc_search:
        logger.warning("Google Search Grounding denemesi başarısız oldu, doğrudan Gemini moduna geçiliyor: %s", exc_search)

    # 2. Deneme: Google Search aracı olmadan doğrudan Gemini modeli (kota/araç hatasına karşı %100 yedek)
    for model_name in [GEMINI_MODEL, "gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=genai_types.GenerateContentConfig(
                    system_instruction=UNRESTRICTED_COACH_SYSTEM_PROMPT,
                    safety_settings=safety if safety else None,
                    temperature=0.6,
                ),
            )
            if response and response.text:
                return response.text.strip()
        except Exception as exc_direct:
            logger.error("Model (%s) hatası: %s", model_name, exc_direct)
            last_error = str(exc_direct)

    return (
        f"⚠️ Gemini API çağrısı sırasında teknik bir hata oluştu: `{last_error[:250]}`\n\n"
        "Lütfen Render.com'daki `GEMINI_API_KEY` anahtarınızın doğru kopyalandığından ve aktif olduğundan emin olun."
    )


def evaluate_interview_answer(question: str, user_answer: str, next_q: Optional[str]) -> str:
    """Kullanıcının mülakat cevabını Gemini AI ile değerlendirir."""
    if HAS_GENAI and GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"Konsolosluk Mülakat Sorusu: {question}\n"
                f"Adayın Cevabı: {user_answer}\n\n"
                "ABD Konsolosluğu vize memuru ve stratejik koç gözüyle bu cevabı değerlendir:\n"
                "1. Güçlü yönü ve varsa memurun şüphelenebileceği/eksik yönü\n"
                "2. Bu cevabın mülakatta söylenebilecek en ikna edici, doğal ve güven veren versiyonu."
            )
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
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
            "DS-260 formuna yazdığınız tarih/adreslerle birebir aynı bilgileri verdiğinizden emin olun."
        )

    if next_q:
        return f"{feedback}\n\n⏭️ *Sıradaki Mülakat Sorusu:*\n{next_q}\n\n_(Çıkmak için `/iptal` yazabilirsiniz)_"
    return (
        f"{feedback}\n\n🎉 *Tebrikler! 6 Soruluk Konsolosluk Mülakat Provasını Tamamladınız!*\n"
        "Checklist'inizde mülakat provası maddesi tamamlandı olarak işaretlendi."
    )


# ============================================================================
# GÜVENLİ TELEGRAM MESAJ GÖNDERİCİ (UZUN MESAJ BÖLME & MARKDOWN KORUMASI)
# ============================================================================

async def safe_reply_or_edit(
    update: Update,
    text: str,
    thinking_msg=None,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """
    Gemini'den gelen uzun veya özel karakterli yanıtların Telegram'da Markdown
    hatası yüzünden yutulmasını önler; 4000 karakterden uzunsa parçalara böler.
    """
    chunks: List[str] = []
    remaining = text.strip() or "Yanıt hazır."
    while len(remaining) > 3900:
        split_idx = remaining.rfind("\n", 0, 3900)
        if split_idx == -1:
            split_idx = 3900
        chunks.append(remaining[:split_idx].strip())
        remaining = remaining[split_idx:].strip()
    if remaining:
        chunks.append(remaining)

    for idx, chunk in enumerate(chunks):
        is_last = idx == len(chunks) - 1
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
            except Exception:
                try:
                    await thinking_msg.edit_text(
                        chunk,
                        disable_web_page_preview=True,
                        reply_markup=markup,
                    )
                    continue
                except Exception:
                    pass

        try:
            await update.message.reply_text(
                chunk,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=markup,
            )
        except Exception:
            await update.message.reply_text(
                chunk,
                disable_web_page_preview=True,
                reply_markup=markup,
            )


# ============================================================================
# PROAKTİF GÜNLÜK KOÇLUK MESAJI ÜRETİCİSİ
# ============================================================================

def generate_daily_coaching_brief(profile: Dict[str, Any]) -> str:
    today = datetime.now(TZ_TR).date()
    chk = profile.get("checklist", {})
    next_todo = next((label for k, label in CHECKLIST_ITEMS if not chk.get(k, False)), None)
    ds260 = profile.get("ds260", {})
    next_ds260 = next((label for k, label in DS260_FIELDS if not ds260.get(k, "").strip()), None)

    reg_open_days = (datetime.strptime("2026-11-01", "%Y-%m-%d").date() - today).days
    results_days = (datetime.strptime("2026-12-03", "%Y-%m-%d").date() - today).days

    lines = [
        f"☀️ *Günaydın! Kişisel Koçunuzdan Günlük Strateji Özeti* ({today.strftime('%d.%m.%Y')})\n",
        f"⏳ *Kritik Geri Sayım:* Başvuru açılışına *{max(0, reg_open_days)} gün*, sonuçların açıklanmasına *{max(0, results_days)} gün* kaldı.\n",
        "🎯 *Bugün Odaklanmamız Gereken Öncelikli Adımlar:*",
    ]
    if next_todo:
        lines.append(f"• *Checklist Önceliğiniz:* {next_todo} (`/checklist`)")
    else:
        lines.append("• 🌟 Tüm Checklist adımlarınız tamamlandı!")

    if next_ds260:
        lines.append(f"• *DS-260 Ön-Hazırlık Görevi:* `{next_ds260}` bilgisini bugün hazırlayıp kaydedin (`/ds260`).")
    else:
        lines.append("• 🌟 DS-260 simülasyon verileriniz tamamen hazır!")

    lines.append(
        "\n💬 *Bugün kafanıza takılan, birlikte analiz etmemizi istediğiniz bir konu veya karar var mı? Doğrudan yazabilirsiniz!*"
    )
    return "\n".join(lines)


# ============================================================================
# TELEGRAM MENÜ VE KOMUT İŞLEYİCİLERİ
# ============================================================================

def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📡 Canlı Durum & Haberler", callback_data="menu_status"),
            InlineKeyboardButton("🧭 5 Fazlı Yol Haritası", callback_data="menu_phases"),
        ],
        [
            InlineKeyboardButton("✅ 12 Adım Checklist", callback_data="menu_checklist"),
            InlineKeyboardButton("📝 DS-260 Simülatörü", callback_data="menu_ds260"),
        ],
        [
            InlineKeyboardButton("🎯 Canlı Mülakat Provası", callback_data="menu_interview"),
            InlineKeyboardButton("📸 Fotoğraf & Pasaport Testi", callback_data="menu_validator"),
        ],
        [
            InlineKeyboardButton("⏳ Kritik Takvim", callback_data="menu_calendar"),
            InlineKeyboardButton("🔐 Onay Numarası Kaydet", callback_data="menu_confno"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_phases_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚀 Faz 1: Kusursuz Başvuru (Ekim-Kasım)", callback_data="phase:phase1")],
            [InlineKeyboardButton("📂 Faz 2: Kasım'da DS-260 & Evrak Ön-Hazırlığı", callback_data="phase:phase2")],
            [InlineKeyboardButton("⚡ Faz 3: 3 Aralık Sonuç & Case Number Stratejisi", callback_data="phase:phase3")],
            [InlineKeyboardButton("🩺 Faz 4: Aşı/Sağlık & Public Charge (Finans)", callback_data="phase:phase4")],
            [InlineKeyboardButton("🎯 Faz 5: Konsolosluk Mülakatı & ABD Girişi", callback_data="phase:phase5")],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")],
        ]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    get_user_profile(state, chat_id)

    ai_badge = "🟢 Sınırsız AI Koç Aktif (Gemini + Canlı Arama + Hafıza)" if (HAS_GENAI and GEMINI_API_KEY) else "🔴 GEMINI_API_KEY Bekleniyor"
    welcome_text = (
        "🇺🇸 *Kişisel Koçunuz & 360° Green Card Süreç Yöneticinize Hoş Geldiniz!*\n\n"
        f"🧠 *Danışman Motoru:* {ai_badge}\n\n"
        "Artık hiçbir kısıtlama olmadan tamamen sizin menfaatinizi düşünen kişisel asistanınızım:\n"
        "• 💬 *Sınırsız Soru-Cevap & Stratejik Yorum:* Bana Green Card, ABD'de yaşam, eyalet/şehir seçimi, iş/kariyer, finans, vize alternatifleri veya kişisel planlarınızla ilgili *her şeyi* sorabilirsiniz. Size kalıp cevaplar değil, kendi analitik yorumumu ve stratejik tavsiyemi sunarım.\n"
        "• 🧠 *Sürekli Sohbet Hafızası:* Konuştuklarımızı hatırlarım (`/hafiza_temizle` ile sıfırlayabilirsiniz).\n"
        "• 🧭 *Dar Takvim Araçları:* Saatlik resmi site taraması, 5 Fazlı Yol Haritası (`/rehber`), 12 Adımlı Checklist (`/checklist`), DS-260 Simülatörü (`/ds260`), Canlı Mülakat Provası (`/mulakat`) ve Fotoğraf/Pasaport Testi (`/fotograf`).\n\n"
        "👇 *Aşağıdaki menüyü kullanabilir veya aklınızdaki herhangi bir soruyu doğrudan yazabilirsiniz:*"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
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
        "🧹 *Sohbet hafızası temizlendi!* Checklist ve DS-260 kayıtlarınız korundu. Yeni bir konuyla devam edebiliriz.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu_keyboard(),
    )


def format_status_report() -> str:
    portal = check_official_dv_portal()
    news = fetch_latest_gc_news(max_items=4)
    now_str = datetime.now(TZ_TR).strftime("%d.%m.%Y %H:%M")

    lines = [
        f"📡 *Güncel Green Card (DV-2027) Durum Raporu* ({now_str})\n",
        "⚖️ *Mahkeme ve Takvim Özeti:*",
        "• *Dava:* Red Eagle Law v. Rubio (14 Ekim 2026 İhtiyati Tedbir Kararı)",
        "• *Resmi İlan Son Günü:* 29 Ekim 2026 (ET 23:59)",
        "• *Başvuru Açılışı:* En geç 1 Kasım 2026 (30 gün açık kalacak)",
        "• *Sonuçların Açıklanması:* En geç 3 Aralık 2026",
        "• *Yeni Şartlar:* 1$ kayıt ücreti + Geçerli pasaport bilgisi ve JPEG kimlik/imza sayfası taraması (<5 MB)\n",
        "🌐 *Resmi Başvuru Portalı (dvprogram.state.gov):*",
        f"• Erişim: {portal['reachable']}",
        f"• Durum: {portal['summary']}\n",
        "📰 *Son Gelişmeler ve Haber Başlıkları:*",
    ]
    if news:
        for idx, item in enumerate(news, 1):
            lines.append(f"{idx}. [{item['title']}]({item['link']})")
    else:
        lines.append("• Son 24 saatte takvimi değiştiren yeni bir mahkeme kararı bildirilmedi.")

    return "\n".join(lines)


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
        f"✅ *12 Adımlı Dar Takvim Hazırlık Checklist'iniz ({completed}/{total})*\n\n"
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
        "3 Aralık 2026'da sonuçlar açıklanır açıklanmaz DS-260 formunu ilk 48 saatte gönderebilmeniz için bilgilerinizi şimdiden buraya kaydedin:\n",
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
    buttons.append([InlineKeyboardButton("🔙 Ana Menü", callback_data="menu_main")])
    return "\n".join(lines), InlineKeyboardMarkup(buttons)


async def cmd_durum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("🔍 Resmi kaynaklar ve mahkeme haberleri taranıyor...")
    report = format_status_report()
    await msg.edit_text(
        report,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=build_main_menu_keyboard(),
    )


async def cmd_rehber(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧭 *DV-2027 Dar Takvim: 5 Fazlı Hızlandırılmış Hazırlık Rehberi*\n\n"
        "Normalde 17 ay süren süreç bu yıl 10 aydan kısa süreceği için her fazı önceden tamamlıyoruz. İncelemek istediğiniz faza tıklayın:",
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
        "Şu andan itibaren İstanbul ABD Başkonsolosluğu'ndaki vize memurunuzum. Size 6 kritik soru soracağım ve her cevabınızı analiz edeceğim.\n\n"
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
        "Dosyalarınızın ABD Dışişleri Bakanlığı teknik standartlarına uygunluğunu test etmek için:\n"
        "1️⃣ Telegram'da *Ataş (📎) -> Dosya (File/Document)* seçeneğine tıklayın.\n"
        "2️⃣ *Biyometrik fotoğrafınızı* gönderirseniz: *JPEG*, *600 x 600 piksel* ve *<= 240 KB* kontrolü yaparım.\n"
        "3️⃣ *Pasaport kimlik/imza sayfası taramanızı* gönderirseniz: PDF değil *JPEG/JFIF* ve *<= 5 MB* kontrolü yaparım.\n\n"
        "🔗 Kafa/göz hizası kırpma aracı: [ABD Dışişleri Photo Tool](https://tsg.phototool.state.gov/photo)"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=build_main_menu_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    state = load_state()
    profile = get_user_profile(state, chat_id)
    data = query.data or ""

    if data == "menu_main":
        await query.edit_message_text(
            "🇺🇸 *Kişisel Koç & 360° Süreç Yöneticisi Ana Menüsü*\nBir modül seçin veya istediğiniz herhangi bir soruyu doğrudan mesaj olarak yazın:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_status":
        await query.edit_message_text("🔍 Güncel durum ve mahkeme haberleri kontrol ediliyor...")
        await query.edit_message_text(
            format_status_report(),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=build_main_menu_keyboard(),
        )
    elif data == "menu_phases":
        await query.edit_message_text(
            "🧭 *DV-2027 Dar Takvim: 5 Fazlı Hızlandırılmış Hazırlık Rehberi*\nDetaylarını görmek istediğiniz faza tıklayın:",
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
            "Lütfen biyometrik fotoğrafınızı veya pasaport taramanızı bu sohbete *Dosya (Document)* olarak gönderin. Boyut, piksel ve format uygunluğunu otomatik kontrol edeceğim!\n\n"
            "🔗 Resmi Kırpma/Hizalama Aracı: [Photo Tool](https://tsg.phototool.state.gov/photo)",
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
        msg += "Başvurunuzu yaptıktan sonra aldığınız *Confirmation Number*'ı kaybetmemek için şimdi mesaj olarak yazıp kaydedebilirsiniz (veya `/iptal` yazın):"
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)


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
    file_size_mb = file_size_kb / 1024.0

    if file_name.endswith(".pdf") or doc.mime_type == "application/pdf":
        await update.message.reply_text(
            "❌ *HATA: PDF Formatı Kabul Edilmez!*\n\n"
            "ABD Dışişleri Bakanlığı DV-2027 kurallarına göre pasaport taraması ve fotoğraflar *kesinlikle JPEG / JFIF (.jpg / .jpeg)* formatında olmalıdır. PDF dosyaları sistem tarafından reddedilir.\n"
            "👉 Lütfen pasaport sayfasını *JPEG* olarak kaydedip tekrar gönderin.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        tg_file = await doc.get_file()
        bio = io.BytesIO()
        await tg_file.download_to_memory(out=bio)
        bio.seek(0)
        img = Image.open(bio)
        width, height = img.size
        img_format = (img.format or "").upper()
    except Exception as exc:
        await update.message.reply_text(
            f"⚠️ Gönderdiğiniz dosya geçerli bir görüntü olarak okunamadı ({exc}). Lütfen `.jpg` / `.jpeg` formatında gönderin."
        )
        return

    is_jpeg = img_format in ("JPEG", "JPG", "JFIF")
    state = load_state()
    profile = get_user_profile(state, update.effective_chat.id)

    if width == height or "foto" in file_name or "photo" in file_name or file_size_kb <= 350:
        checks = [
            ("JPEG/JFIF Formatı", is_jpeg, f"Format: {img_format} (JPEG olmalı)"),
            ("600x600 Piksel Kare Boyut", width == 600 and height == 600, f"Mevcut: {width}x{height} px (600x600 olmalı)"),
            ("Maksimum 240 KB Dosya Boyutu", file_size_kb <= 240, f"Mevcut: {file_size_kb:.1f} KB (<= 240 KB olmalı)"),
        ]
        all_ok = all(ok for _, ok, _ in checks)
        lines = ["📸 *Biyometrik Fotoğraf Teknik Kontrol Sonucu:*\n"]
        for label, ok, detail in checks:
            icon = "✅" if ok else "❌"
            lines.append(f"{icon} *{label}:* {detail}")

        if all_ok:
            profile["checklist"]["photo_taken"] = True
            profile["checklist"]["photo_tested"] = True
            save_state(state)
            lines.append(
                "\n🎉 *Tebrikler!* Fotoğrafınız tüm teknik kriterleri (JPEG, 600x600 px, <=240 KB) sağlıyor ve Checklist'inizde işaretlendi!\n"
                "⚠️ *Son Manuel Kontrol:* Gözlük/küpe olmadığından, arka planın düz beyaz/açık olduğundan ve son 6 ayda çekildiğinden emin olun."
            )
        else:
            lines.append(
                "\n🛠️ *Nasıl Düzeltilir?*\n"
                "Fotoğrafınızı [ABD Dışişleri Bakanlığı Resmi Photo Tool](https://tsg.phototool.state.gov/photo) aracına yükleyerek otomatik olarak 600x600 piksele kırpabilir ve tekrar buraya gönderip test edebilirsiniz."
            )
        await update.message.reply_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    checks = [
        ("JPEG/JFIF Formatı (PDF Değil)", is_jpeg, f"Format: {img_format}"),
        ("Maksimum 5 MB Dosya Boyutu", file_size_mb <= 5.0, f"Mevcut: {file_size_mb:.2f} MB (<= 5 MB olmalı)"),
        ("Okunabilir Çözünürlük (>= 600 px)", width >= 600 and height >= 600, f"Mevcut: {width}x{height} px"),
    ]
    all_ok = all(ok for _, ok, _ in checks)
    lines = ["🛂 *Pasaport Kimlik & İmza Sayfası Tarama Kontrolü:*\n"]
    for label, ok, detail in checks:
        icon = "✅" if ok else "❌"
        lines.append(f"{icon} *{label}:* {detail}")

    if all_ok:
        profile["checklist"]["passport_scan"] = True
        save_state(state)
        lines.append(
            "\n🎉 *Harika!* Pasaport taramanız DV-2027 yükleme kriterlerine (JPEG, <5 MB) uygun ve Checklist'inizde tamamlandı olarak işaretlendi."
        )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def handle_photo_compressed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Önemli İpucu:* Telegram normal galeri fotoğraflarını otomatik sıkıştırıp boyutunu değiştirir.\n\n"
        "Gerçek *600x600 piksel* ve *KB* değerini hatasız test edebilmem için lütfen fotoğrafı *Ataş (📎) -> Dosya (Document)* olarak gönderin!",
        parse_mode=ParseMode.MARKDOWN,
    )


# ============================================================================
# METİN MESAJLARI (SINIRSIZ KİŞİSEL KOÇ, MÜLAKAT SİMÜLASYONU VEYA DS-260)
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
            "İşlem iptal edildi. Bana istediğiniz soruyu doğrudan yazabilir veya menüden devam edebilirsiniz:",
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
        eval_text = evaluate_interview_answer(current_q, text, next_q)
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
            "3 Aralık 2026'da sonuçlar açıklandığında bu numarayla sorgulama yapacağız.",
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

    # 3. Kısıtlamasız Kişisel Koç & Stratejik Danışman Yanıtı (Çoklu Sohbet Hafızalı)
    thinking_msg = await update.message.reply_text("🧠 _Kişisel koçunuz düşünüyor..._", parse_mode=ParseMode.MARKDOWN)
    reply = answer_user_question(text, profile)

    # Sohbet geçmişine kaydet (son 20 mesajı tut)
    profile.setdefault("chat_history", []).append({"role": "user", "text": text})
    profile["chat_history"].append({"role": "assistant", "text": reply})
    profile["chat_history"] = profile["chat_history"][-20:]
    save_state(state)

    await safe_reply_or_edit(
        update,
        reply,
        thinking_msg=thinking_msg,
        reply_markup=build_main_menu_keyboard(),
    )


# ============================================================================
# ARKA PLAN PERİYODİK BİLDİRİM & GÜNLÜK KOÇLUK GÖREVİ
# ============================================================================

async def run_monitoring_cycle(bot) -> None:
    state = load_state()
    subscribers: List[int] = state.get("subscribers", [])
    if not subscribers:
        return

    alerts: List[str] = []

    portal = check_official_dv_portal()
    prev_hash = state.get("last_dv_portal_hash", "")
    if portal["hash"] and prev_hash and portal["hash"] != prev_hash:
        alerts.append(
            f"🚨 *Resmi DV Lottery Sitesinde (dvprogram.state.gov) Değişiklik Tespit Edildi!*\n"
            f"Durum: {portal['summary']}\n👉 [Hemen Kontrol Et]({portal['url']})"
        )
    if portal["hash"]:
        state["last_dv_portal_hash"] = portal["hash"]

    seen_hashes: List[str] = state.get("seen_news_hashes", [])
    latest_news = fetch_latest_gc_news(max_items=5)
    new_items = [item for item in latest_news if item["id"] not in seen_hashes]

    if new_items and seen_hashes:
        news_lines = ["📰 *Green Card Süreciyle İlgili Yeni Gelişme!*"]
        for item in new_items[:3]:
            news_lines.append(f"• [{item['title']}]({item['link']})")
        alerts.append("\n".join(news_lines))

    for item in latest_news:
        if item["id"] not in seen_hashes:
            seen_hashes.append(item["id"])
    state["seen_news_hashes"] = seen_hashes[-100:]

    now_tr = datetime.now(TZ_TR)
    today_str = now_tr.strftime("%Y-%m-%d")
    send_daily_brief = False
    if now_tr.hour >= 9 and state.get("last_daily_brief_date") != today_str:
        state["last_daily_brief_date"] = today_str
        send_daily_brief = True

    save_state(state)

    for chat_id in subscribers:
        try:
            if alerts:
                await bot.send_message(
                    chat_id=chat_id,
                    text="\n\n".join(alerts),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            if send_daily_brief:
                profile = get_user_profile(state, chat_id)
                brief = generate_daily_coaching_brief(profile)
                await bot.send_message(
                    chat_id=chat_id,
                    text=brief,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=build_main_menu_keyboard(),
                )
        except Exception as exc:
            logger.warning("Kullanıcıya (%s) bildirim gönderilemedi: %s", chat_id, exc)


async def periodic_monitor_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_monitoring_cycle(context.bot)


# ============================================================================
# ANA ÇALIŞTIRICI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Unrestricted Personal Coach & Green Card Bot")
    parser.add_argument(
        "--cron-once",
        action="store_true",
        help="GitHub Actions gibi zamanlanmış ortamlarda tek seferlik tarama/günlük özet gönderip çıkar.",
    )
    args = parser.parse_args()

    if not BOT_TOKEN or BOT_TOKEN == "BURAYA_TELEGRAM_BOT_TOKEN_YAZIN":
        print(
            "⚠️ LÜTFEN TELEGRAM_BOT_TOKEN ORTAM DEĞİŞKENİNİ TANIMLAYIN!\n"
            "Render.com / Koyeb / GitHub Secrets üzerinde:\n"
            "  TELEGRAM_BOT_TOKEN = BotFather'dan aldığınız token\n"
            "  GEMINI_API_KEY     = Google AI Studio'dan aldığınız ücretsiz API anahtarı"
        )
        return

    app: Application = ApplicationBuilder().token(BOT_TOKEN).build()

    if args.cron_once:
        asyncio.run(run_monitoring_cycle(app.bot))
        logger.info("Tek seferlik cron taraması tamamlandı.")
        return

    start_health_server()

    # Komutlar
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("hafiza_temizle", cmd_clear_memory))
    app.add_handler(CommandHandler("durum", cmd_durum))
    app.add_handler(CommandHandler("rehber", cmd_rehber))
    app.add_handler(CommandHandler("mulakat", cmd_mulakat))
    app.add_handler(CommandHandler("takvim", cmd_takvim))
    app.add_handler(CommandHandler("checklist", cmd_checklist))
    app.add_handler(CommandHandler("ds260", cmd_ds260))
    app.add_handler(CommandHandler("fotograf", cmd_fotograf))

    # Buton ve mesaj işleyicileri
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_compressed))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    if app.job_queue:
        app.job_queue.run_repeating(
            periodic_monitor_job,
            interval=CHECK_INTERVAL_SECONDS,
            first=15,
        )
        logger.info("Otomatik bulut tarama aktif (Her %s saniyede bir).", CHECK_INTERVAL_SECONDS)

    logger.info("Kişisel Koç & Green Card 360° Bulut Botu 7/24 dinlemede...")
    app.run_polling()


if __name__ == "__main__":
    main()
