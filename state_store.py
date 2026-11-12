"""Persistent PostgreSQL if DATABASE_URL is defined; atomic local fallback otherwise."""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

_log = logging.getLogger("GreenCardCloudCoach")


def default_state() -> Dict[str, Any]:
    return {"subscribers": [], "seen_news_hashes": [], "users": {}}


def get_storage_status(path: Optional[Path] = None) -> Dict[str, Any]:
    """Returns database connection status and fallback storage health."""
    url = os.getenv("DATABASE_URL", "").strip()
    status = {
        "postgres_configured": bool(url),
        "postgres_connected": False,
        "active_backend": "local_json",
        "error": None,
    }
    if url:
        try:
            import psycopg
            with psycopg.connect(url, connect_timeout=3) as con:
                with con.cursor() as cur:
                    cur.execute("SELECT 1")
                status["postgres_connected"] = True
                status["active_backend"] = "postgresql"
        except Exception as exc:
            status["error"] = f"{type(exc).__name__}: {exc}"
    return status


def load(path: Path) -> Dict[str, Any]:
    """Load state from PostgreSQL if available; fallback to local atomic JSON."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        try:
            import psycopg
            with psycopg.connect(url, connect_timeout=6) as con:
                with con.cursor() as cur:
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS greencard27_state "
                        "(id INTEGER PRIMARY KEY, payload JSONB NOT NULL)"
                    )
                    cur.execute("SELECT payload FROM greencard27_state WHERE id=1")
                    row = cur.fetchone()
                    if row and isinstance(row[0], dict):
                        return row[0]
                    return default_state()
        except Exception as exc:
            _log.warning("PostgreSQL load başarısız (%s); yerel JSON dosyasına geçiliyor.", exc)

    if path and path.exists():
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            return content if isinstance(content, dict) else default_state()
        except (OSError, ValueError) as exc:
            _log.warning("Yerel JSON durum okunamadı: %s", exc)
    return default_state()


def save(path: Path, data: Dict[str, Any]) -> None:
    """Save state to PostgreSQL if available, and always persist to local atomic JSON as backup."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        try:
            import psycopg
            from psycopg.types.json import Jsonb
            with psycopg.connect(url, connect_timeout=6) as con:
                with con.cursor() as cur:
                    cur.execute(
                        "CREATE TABLE IF NOT EXISTS greencard27_state "
                        "(id INTEGER PRIMARY KEY, payload JSONB NOT NULL)"
                    )
                    cur.execute(
                        "INSERT INTO greencard27_state(id, payload) VALUES(1, %s) "
                        "ON CONFLICT(id) DO UPDATE SET payload=EXCLUDED.payload",
                        [Jsonb(data)],
                    )
        except Exception as exc:
            _log.warning("PostgreSQL save başarısız (%s); yerel JSON dosyasına yazılıyor.", exc)

    # Her halükarda yerel atomik JSON yedeğini de güncelle (container veya bağlantı kesintisine karşı)
    if path:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
        except Exception as exc:
            _log.warning("Yerel JSON durum yazılamadı: %s", exc)
