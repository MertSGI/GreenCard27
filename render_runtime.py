"""Authenticated Telegram webhook + Render health server; no polling."""
import asyncio
import hashlib
import hmac
import logging
import os
import signal
from datetime import datetime, timezone
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
        self.last_update_utc = None

    def health_payload(self) -> dict:
        running = self.ready and self.application.running
        return {
            "service": "GreenCard27",
            "status": "ok" if running else "starting",
            "telegram_transport": "webhook",
            "webhook_registered": self.ready,
            "updates_received": self.updates_received,
            "last_update_utc": self.last_update_utc,
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    async def health(self, request: web.Request) -> web.Response:
        p = self.health_payload()
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
        except (ValueError, UnicodeDecodeError):
            logger.warning("Telegram webhook: bozuk payload reddedildi.")
            raise web.HTTPBadRequest()
        await self.application.update_queue.put(update)
        self.updates_received += 1
        self.last_update_utc = datetime.now(timezone.utc).isoformat()
        logger.info("Telegram webhook mesajı: update_id=%s, toplam=%s",
                    update.update_id, self.updates_received)
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
            await application.bot.set_webhook(
                url=state.webhook_url, secret_token=state.secret,
                drop_pending_updates=False, max_connections=8,
            )
            state.ready = True
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
