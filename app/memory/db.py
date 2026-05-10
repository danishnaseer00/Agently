from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "data" / "conversations.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)")
        conn.commit()


def save_conversation(
    conv_id: str,
    title: str,
    created_at: str,
    updated_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO conversations (id, title, created_at, updated_at)
               VALUES (?, ?, ?, ?)""",
            (conv_id, title, created_at, updated_at),
        )
        conn.commit()


def save_message(
    msg_id: str,
    conv_id: str,
    role: str,
    content: str,
    created_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO messages (id, conversation_id, role, content, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (msg_id, conv_id, role, content, created_at),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (created_at, conv_id),
        )
        conn.commit()


def get_conversations(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_conversation_messages(conv_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_conversation(conv_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()


def update_conversation_title(conv_id: str, title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now().isoformat(), conv_id),
        )
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")