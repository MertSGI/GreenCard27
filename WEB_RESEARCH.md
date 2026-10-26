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

## Hukukçu ve Forum Görüşleri
- `/yorumlar`: DV-2027 / Red Eagle Law davası için hukukçuların yazılarını, Reddit ve forum tartışmalarını araştırır.
- `/yorumlar DV-2028 ile ilgili ne düşünüyorlar`: konuyu özelleştirir.
- Normal sohbet içinde `avukatlar`, `forum`, `Reddit`, `kullanıcılar ne diyor` gibi ifadeler de görüş araştırmasını açar.
- .gov doğrulaması gayriresmî görüşleri aktarmanın ön koşulu değildir. Kaynaklar kendi türüyle etiketlenir.
- Gemini çalışmazsa mevcut arama bulguları doğrudan özetlenir; checklist otomatik eklenmez.
- Arama sağlayıcıları engellenebilir; sonuç yoksa bu teknik sınırlama olarak açıklanır.
