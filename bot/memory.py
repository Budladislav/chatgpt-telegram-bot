# memory.py
import sqlite3, time, os
from typing import List, Dict, Tuple

DB_PATH = os.getenv("MEMORY_DB_PATH", "data/memory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,            -- 'user' | 'assistant' | 'system'
  content TEXT NOT NULL,
  ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
  user_id TEXT PRIMARY KEY,
  info TEXT NOT NULL,            -- произвольный текст профиля (о тебе)
  updated_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS summaries (
  user_id TEXT PRIMARY KEY,
  summary TEXT NOT NULL,
  upto_msg_id INTEGER NOT NULL,
  updated_ts INTEGER NOT NULL
);
"""

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("PRAGMA journal_mode=WAL;")
    return c

def init():
    with _conn() as c:
        for stmt in SCHEMA.strip().split(";\n"):
            if stmt.strip():
                c.execute(stmt)

def save_message(user_id: str, role: str, content: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO messages(user_id, role, content, ts) VALUES (?,?,?,?)",
            (user_id, role, content, int(time.time()))
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]

def get_recent_messages(user_id: str, limit: int = 20) -> List[Tuple[int,str,str,str,int]]:
    with _conn() as c:
        return c.execute(
            "SELECT id,user_id,role,content,ts FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()[::-1]

def upsert_profile(user_id: str, info: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO profiles(user_id, info, updated_ts) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET info=excluded.info, updated_ts=excluded.updated_ts",
            (user_id, info, int(time.time()))
        )

def get_profile(user_id: str) -> str:
    with _conn() as c:
        row = c.execute("SELECT info FROM profiles WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else ""

def get_summary(user_id: str) -> Tuple[str,int]:
    with _conn() as c:
        row = c.execute("SELECT summary,upto_msg_id FROM summaries WHERE user_id=?", (user_id,)).fetchone()
        return (row[0], row[1]) if row else ("", 0)

def save_summary(user_id: str, summary: str, upto_msg_id: int):
    with _conn() as c:
        c.execute(
            "INSERT INTO summaries(user_id, summary, upto_msg_id, updated_ts) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET summary=excluded.summary, upto_msg_id=excluded.upto_msg_id, updated_ts=excluded.updated_ts",
            (user_id, summary, upto_msg_id, int(time.time()))
        )
