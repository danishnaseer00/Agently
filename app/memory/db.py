from __future__ import annotations
import sqlite3
from pathlib import Path

def get_connection(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)
