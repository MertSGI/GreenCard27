"""Authenticated Telegram webhook + Render health server; no polling."""
import asyncio
import hashlib
import hmac
import logging
import os
import signal
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

from aiohttp import web
from telegram import Update

logger = logging.getLogger("GreenCardCloudCoach")


def webhook_identity(token: str) -> tuple[str, str]:
    if not token:
        raise ValueError("Telegram bot token eksik")
    path = "/tg/" + hashlib.sha256(("route:" + token).encode()).hexdigest()[:32]
    secret = hashlib.sha256(("secret:" + token).encode()).hexdigest()
    return path, secret


def resolve_base_url() -> str:
    url = (os.getenv("WEBHOOK_BASE_URL", "").strip()
           or os.getenv("RENDER_EXTERNAL_URL", "").strip()).rstrip("/")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        raise RuntimeError("Render HTTPS URL bulunamadı; RENDER_EXTERNAL_URL gerekli.")
    return url


class BotWebhookRuntime:
    def __init__(self, application, token: str, base_url: str):
        self.application = application
        self.path, derived_secret = webhook_identity(token)
        self.secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip() or derived_secret
        self.webhook_url = base_url + self.path
        self.ready = False
        self.updates_received = 0
        self.last_update_utc: Optional[str] = None
        self.last_update_info: Optional[Dict[str, Any]] = None
        self.last_handler_error: Optional[Dict[str, Any]] = None

    def health_payload(self) -> dict:
        """Sync payload for unit tests and simple status checks."""
        running = self.ready and getattr(self.application, "running", False)
        return {
            "service": "GreenCard27",
            "status": "ok" if running else "starting",
            "telegram_transport": "webhook",
            "webhook_registered": self.ready,
            "updates_received": self.updates_received,
            "last_update_utc": self.last_update_utc,
            "deployed_sha": os.getenv("RENDER_GIT_COMMIT", ""),
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    async def get_health_data(self) -> dict:
        """Comprehensive async diagnostic payload with live webhook info and DB health."""
        base = self.health_payload()

        # Database health check
        try:
            from state_store import get_storage_status
            base["database"] = get_storage_status()
        except Exception as exc:
            base["database"] = {"error": str(exc)}

        # Active AI model / Gemini status
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        base["gemini"] = {
            "api_key_configured": bool(gemini_key),
            "preferred_model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        }

        # Telegram Bot API Webhook Status
        wh_info = None
        bot = getattr(self.application, "bot", None)
        if bot:
            try:
                info = await bot.get_webhook_info()
                wh_info = {
                    "url": info.url,
                    "has_custom_certificate": info.has_custom_certificate,
                    "pending_update_count": info.pending_update_count,
                    "last_error_date": info.last_error_date.isoformat() if info.last_error_date else None,
                    "last_error_message": info.last_error_message,
                    "max_connections": info.max_connections,
                }
            except Exception as exc:
                wh_info = {"query_error": f"{type(exc).__name__}: {exc}"}
        base["telegram_webhook"] = wh_info

        # Recent update details & last handler error
        base["last_update_info"] = self.last_update_info
        last_err = getattr(self.application, "_last_handler_error", None) or self.last_handler_error
        base["last_handler_error"] = last_err

        return base

    async def health(self, request: web.Request) -> web.Response:
        p = await self.get_health_data()
        return web.json_response(p, status=200 if p["status"] == "ok" else 503)

    async def receive(self, request: web.Request) -> web.Response:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(header, self.secret):
            logger.warning("Telegram webhook: doğrulanmamış istek reddedildi.")
            raise web.HTTPForbidden()
        if not self.ready:
            raise web.HTTPServiceUnavailable()
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise ValueError("Expected object")
            update = Update.de_json(payload, self.application.bot)
            if update is None:
                raise ValueError("Missing update")
        except (ValueError, UnicodeDecodeError) as exc:
            logger.warning("Telegram webhook: bozuk payload reddedildi: %s", exc)
            raise web.HTTPBadRequest()

        self.updates_received += 1
        self.last_update_utc = datetime.now(timezone.utc).isoformat()

        text_snip = None
        up_type = "other"
        if update.message:
            up_type = "message"
            if update.message.text:
                text_snip = update.message.text[:60]
            elif update.message.photo:
                up_type = "photo"
            elif update.message.document:
                up_type = "document"
        elif update.callback_query:
            up_type = "callback"
            text_snip = update.callback_query.data

        self.last_update_info = {
            "update_id": update.update_id,
            "type": up_type,
            "text": text_snip,
            "chat_id": update.effective_chat.id if update.effective_chat else None,
            "time_utc": self.last_update_utc,
        }
        logger.info(
            "Telegram webhook mesajı: update_id=%s, type=%s, toplam=%s",
            update.update_id, up_type, self.updates_received,
        )

        await self.application.update_queue.put(update)
        return web.json_response({"ok": True})


async def _run(application, token: str, port: int):
    state = BotWebhookRuntime(application, token, resolve_base_url())
    server = web.Application(client_max_size=512 * 1024)
    server.router.add_get("/", state.health)
    server.router.add_get("/health", state.health)
    server.router.add_post(state.path, state.receive)
    runner = web.AppRunner(server, access_log=None)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except (NotImplementedError, RuntimeError, ValueError):
            pass
    async with application:
        await application.start()
        try:
            await runner.setup()
            await web.TCPSite(runner, "0.0.0.0", port).start()
            logger.info("Render /health servisi port=%s açıldı.", port)
            # Port bağlandığı andan itibaren hazır olarak işaretle (503 retry storm önlenir)
            state.ready = True
            await application.bot.set_webhook(
                url=state.webhook_url, secret_token=state.secret,
                drop_pending_updates=False, max_connections=8,
            )
            logger.info("Telegram HTTPS webhook başarıyla kaydedildi; polling kapalı.")
            try:
                info = await application.bot.get_webhook_info()
                logger.info("Telegram webhook kontrolü: aktif=%s, bekleyen=%s, son_hata=%s",
                            bool(info.url), info.pending_update_count, info.last_error_date)
            except Exception as exc:
                logger.warning("Webhook bilgi sorgusu başarısız: %s", type(exc).__name__)
            await stop.wait()
        finally:
            state.ready = False
            await runner.cleanup()
            await application.stop()
            logger.info("Webhook uygulaması kapandı.")


def run_render_webhook(application, bot_token: str, port: int) -> None:
    try:
        asyncio.run(_run(application, bot_token, port))
    except KeyboardInterrupt:
        pass
