"""Persistent PostgreSQL if DATABASE_URL is defined; atomic local fallback otherwise."""
import json
import logging
import os
from pathlib import Path
_log=logging.getLogger("GreenCardCloudCoach")

def default_state():
    return {"subscribers":[],"seen_news_hashes":[],"users":{}}

def load(path: Path):
    url=os.getenv("DATABASE_URL","").strip()
    if url:
        import psycopg
        with psycopg.connect(url,connect_timeout=6) as con:
            with con.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS greencard27_state (id INTEGER PRIMARY KEY,payload JSONB NOT NULL)")
                cur.execute("SELECT payload FROM greencard27_state WHERE id=1")
                row=cur.fetchone()
                return row[0] if row else default_state()
    if path.exists():
        try:
            content=json.loads(path.read_text(encoding="utf-8"))
            return content if isinstance(content,dict) else default_state()
        except (OSError,ValueError):
            _log.warning("Yerel JSON durum okunamadı.")
    return default_state()

def save(path: Path,data):
    url=os.getenv("DATABASE_URL","").strip()
    if url:
        import psycopg
        from psycopg.types.json import Jsonb
        with psycopg.connect(url,connect_timeout=6) as con:
            with con.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS greencard27_state (id INTEGER PRIMARY KEY,payload JSONB NOT NULL)")
                cur.execute("INSERT INTO greencard27_state(id,payload) VALUES(1,%s) ON CONFLICT(id) DO UPDATE SET payload=EXCLUDED.payload",[Jsonb(data)])
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    tmp.replace(path)
