# GreenCard27 RUNBOOK

### Temel Telegram Komutları:
- `/start`: Botu başlatır, ana menüyü ve özellikleri tanıtır.
- `/hafiza_temizle`: Sohbet hafızasını temizler; checklist ve DS-260 kayıtlarını korur.
- `/bugun`: Günlük kişisel adımlar ve somut eylem planı.
- `/bildirim_test`: Günlük koçluk bildirimini anında test eder.
- `/ara <konu>`: Canlı web araştırması yapar (pasaport/özel veri içermez).
- `/yorumlar [konu]`: Göçmenlik avukatları, Reddit ve forum görüşlerini analiz eder.
- `/durum`: Resmî kaynaklar ve mahkeme durum raporu.
- `/rehber`: 5 Fazlı Hızlandırılmış Hazırlık Rehberi.
- `/mulakat`: 6 soruluk canlı Konsolosluk Mülakat Simülasyonu.
- `/checklist`: 12 adımlı interaktif hazırlık kontrol listesi.
- `/ds260`: DS-5501 / DS-260 kişisel veri hazırlık simülatörü.
- `/fotograf`: Biyometrik fotoğraf (600x600 px, <=240 KB) ve pasaport taraması (<5 MB, JPEG) otomatik denetleyici.
- `/ai_durum`: Canlı Gemini API bağlantısı ve model teşhisi.
- `/id`: Telegram Chat ID'nizi gösterir.

### Bulut ve Yerel Çalıştırma:
- **Render.com:** `TELEGRAM_BOT_TOKEN` ve `GEMINI_API_KEY` tanımlı olmalıdır. Render ortamında `RENDER_EXTERNAL_URL` otomatik olarak algılanır ve kimlik doğrulamalı HTTPS Webhook (`/tg/...`) ile `/health` servisi çalıştırılır.
- **Yerel Çalışma:** `RENDER_EXTERNAL_URL` bulunmadığında bot otomatik olarak güvenli Polling + dahili Health-Check sunucusu moduna geçer.
- **Kalıcı Hafıza:** `DATABASE_URL` (PostgreSQL) tanımlanırsa tüm checklist, DS-260 ve sohbet hafızası veritabanında kalıcı tutulur. Tanımlanmazsa yerel atomik JSON (`state_store.py`) kullanılır.
- **Sabah Özeti:** Render yeniden başlamalarında da hedefe bildirim gidebilmesi için `COACH_CHAT_ID=/id` çıktısı eklenebilir.

### Deployed SHA Kontrolü:
`/health` yanıtındaki `deployed_sha`, Render servisinin şu anda çalıştırdığı `RENDER_GIT_COMMIT` değeridir. GitHub commit'i ile aynı değilse deploy henüz güncel değildir.
