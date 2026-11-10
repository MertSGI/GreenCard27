# GreenCard27 RUNBOOK

### Temel Telegram Komutları:
- `/start`: Botu başlatır, ana menüyü ve özellikleri tanıtır.
- `/aksiyon` (veya `/strateji`): "Benim Yerine Düşün" proaktif senaryo motoru — sıra numarası, meslek (221g TAL riski), bütçe (Public Charge), DS-260 ve takvim darlığını analiz ederek olası senaryoları ve hazır İngilizce KCC/Konsolosluk maillerini sunar.
- `/case [numara]`: DV Case Number Proaktif Analizörü (Örn: `2027EU00028500` veya `EU28500`) — Sıra numarası dilimi, 3 olası senaryo, acil aksiyonlar ve KCC'ye *"onlara şu şekilde söyleyelim"* hazır İngilizce durum/hazırlık maili + interaktif resmi yazışma butonları.
- `/haber_analiz`: Günün en güncel 2 haberini çeker ve 'bu şekilde olabilir / böyle hazır olmalıyız' stratejik senaryosuyla yorumlar.
- `/dosya_tasima [senaryo]`: 2025-2026 güncel kurallarıyla konsolosluk dosya taşıma stratejisi ve kişiye özel İngilizce resmi dilekçe üretir (KCC / Consular / Unlock / Expedited Appointment).
- `/vize_analiz`: Profilinize göre 360° Amerikan Vizesi uygunluk raporu (DV, EB-2 NIW, O-1, E-2, F-1, B1/B2 214b, H-1B, L-1).
- `/mahkeme`: Red Eagle Law v. Rubio davası, 9. Temyiz Mahkemesi (Ninth Circuit) kararı, portal açılış olasılıkları ve 3 takvim senaryosu analizi.
- `/surec`: 360° A'dan Z'ye Green Card Yaşam Döngüsü (DS-5501 başvurusundan ABD'de ilk 90 güne kadar 10 aşamalı rehber).
- `/bugun`: Günlük kişisel adımlar, takvim durumu ve günün 2 haberinin stratejik yorumu.
- `/karne`: 360° Hazırlık ve DS-260 Risk Karnesi (100 üzerinden puanlama, kritik açıklar ve en acil 3 eylem adımı).
- `/hesapla [bütçe] [eyalet]`: ABD Taşınma Maliyeti & Runway Hesaplayıcı (Uçak, depozito, araç, harçlar, aylık gider ve kaç ay yeteceği analizi).
- `/eyalet [eyalet1] [eyalet2]`: ABD Eyalet & Şehir Karşılaştırma Rehberi (Gelir vergisi, kira, tech/sağlık maaşları, Türk topluluğu, iklim).
- `/vize_rotalari`: Alternatif ABD Vizeleri ve B Planı (EB-2 NIW, O-1, H-1B, L-1, F-1 STEM OPT, E-2 profiline göre öneriler).
- `/sozluk [terim]`: Green Card & ABD Göçmenlik Terimleri Sözlüğü (CEAC, 2NL, 221(g), KCC, Public Charge, Form I-134 vb.).
- `/mulakat`: 6 soruluk canlı Konsolosluk Mülakat Simülasyonu ve detaylı 3 boyutlu koç geri bildirimi.
- `/fotograf`: Biyometrik fotoğraf (600x600 px, <=240 KB, sRGB, arka plan beyazlık/aydınlık testi) ve pasaport taraması (<5 MB, JPEG) derin teknik denetleyici.
- `/profilim`: Kişisel profil hafızanızı görüntüler (meslek, bütçe, aile, hedef lokasyon, eğitim, İngilizce, case number, ehliyet, vize geçmişi).
- `/profil <alan> <bilgi>`: Manuel olarak profil bilgisi günceller (ör. `/profil butce 25.000$`, `/profil hedef Austin, Texas`, `/profil case 2027EU00014250`).
- `/profil_temizle`: Saklanan tüm kişisel profil hafızasını sıfırlar.
- `/checklist`: 12 adımlı interaktif hızlandırılmış hazırlık kontrol listesi.
- `/ds260`: DS-5501 / DS-260 kişisel veri hazırlık simülatörü.
- `/ara <konu>`: Canlı web araştırması yapar (pasaport/özel veri içermez).
- `/yorumlar [konu]`: Göçmenlik avukatları, Reddit ve forum görüşlerini analiz eder.
- `/durum`: Resmî kaynaklar ve mahkeme durum raporu.
- `/rehber`: 5 Fazlı Hızlandırılmış Hazırlık Rehberi.
- `/hafiza_temizle`: Kısa süreli sohbet hafızasını temizler; checklist, DS-260 ve profil kayıtlarını korur.
- `/ai_durum`: Canlı Gemini API bağlantısı ve model teşhisi.
- `/bildirim_test`: Günlük koçluk bildirimini anında test eder.
- `/id`: Telegram Chat ID'nizi gösterir.

### Bulut ve Yerel Çalıştırma:
- **Render.com:** `TELEGRAM_BOT_TOKEN` ve `GEMINI_API_KEY` tanımlı olmalıdır. Render ortamında `RENDER_EXTERNAL_URL` otomatik olarak algılanır ve kimlik doğrulamalı HTTPS Webhook (`/tg/...`) ile `/health` servisi çalıştırılır.
- **Yerel Çalışma:** `RENDER_EXTERNAL_URL` bulunmadığında bot otomatik olarak güvenli Polling + dahili Health-Check sunucusu moduna geçer.
- **Kalıcı Hafıza:** `DATABASE_URL` (PostgreSQL) tanımlanırsa tüm checklist, DS-260, profil ve sohbet hafızası veritabanında kalıcı tutulur. Tanımlanmazsa yerel atomik JSON (`state_store.py`) kullanılır.
- **Sabah Özeti:** Render yeniden başlamalarında da hedefe bildirim gidebilmesi için `COACH_CHAT_ID=/id` çıktısı eklenebilir.

### Deployed SHA Kontrolü:
`/health` yanıtındaki `deployed_sha`, Render servisinin şu anda çalıştırdığı `RENDER_GIT_COMMIT` değeridir. GitHub commit'i ile aynı değilse deploy henüz güncel değildir.
