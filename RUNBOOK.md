GreenCard27 RUNBOOK

/start: abone ol; /id: Telegram Chat ID; /bugun: günlük kişisel adımlar; /bildirim_test: bildirimi hemen gör; /ara: web araştırması; /ai_durum: Gemini bağlantısı.

Render: TELEGRAM_BOT_TOKEN ve GEMINI_API_KEY mevcut olmalı. Sabah özetinin Render yeniden başlamasından sonra da hedefe gidebilmesi için COACH_CHAT_ID=/id çıktısı eklenmeli. DATABASE_URL verilirse bot PostgreSQL ile kalıcı kullanıcı kayıtlarını tutar. Verilmezse Render geçici diskinde checklist yeniden başlamalarda kaybolabilir.

GitHub render-heartbeat.yml her 10 dakikada Render servisini uyandırmayı dener. GitHub cron işlerindeki gecikmeler nedeniyle kesin dakikada teslim garantisi yoktur. Sabah özeti 09:00 sonrası ilk uygun çalışmada bir kez gönderilir (kalıcı DB yoksa yeniden başlatma aynı gün tekrar gönderebilir). Haber başlıkları resmî karar olarak sunulmaz. Gizli tokenları paylaşmayın.
