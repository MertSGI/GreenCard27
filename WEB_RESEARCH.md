# GreenCard27 – ücretsiz canlı web araştırması

## Komutlar
- \`/ara DV-2027 başvuru tarihleri\`: Gerçek zamanlı ücretsiz web araması + Gemini ile yorum (Gemini erişilemezse kaynak bağlantıları ve yerleşik uyarı).
- Normal sohbet mesajları: Green Card konusuna göre, kişisel profil veya DS-260 verileri paylaşılmadan otomatik genel web taraması.
- \`/durum\`: Canlı kaynak bağlantılarını gösterir; resmî site açıldı iddiasında bulunmaz.
- \`/ai_durum\`: Kullanılabilir Gemini modelini test eder.

## Render
Yeni ücretsiz arama anahtarı gerekmiyor. \`WEB_RESEARCH_ENABLED=true\` (varsayılan) ve \`GEMINI_API_KEY\` (mevcut) yeterli.
\`pip install -r requirements.txt\` yeni \`ddgs\` bağımlılığını yükler.
Değişiklikten sonra en son main commit'i deploy edin.

## Sınırlar
- Arama motoru bağımlılığı rate-limit/bloklanma yaşayabilir; Google News RSS yedek yalnız haber başlıkları getirir.
- Arama sonucu gerçek hukuki onay değildir; .gov bağlantılarında duyuru tarihi ve metnin tamamı ayrıca okunmalıdır.
- Kayıtların Telegram/Render'da kalıcı güvenliği ayrı P0 çalışmasıdır: pasaport numarası, adres, confirmation no gibi değerleri /ara içinde yazmayın.
- Ücretli Google Search grounding default kapalıdır, ücretli fallback yoktur.
- Canlı web araması ücretsiz olduğundan ticari SLA garantisi yoktur; başarısız aramalar dürüstçe bildirilir.
