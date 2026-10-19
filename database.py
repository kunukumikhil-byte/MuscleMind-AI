"""Database helpers for local SQLite development and Vercel's temporary filesystem."""
import os
import sqlite3
from pathlib import Path


def database_path():
    # Set DATABASE_PATH to a persistent mounted path locally or on a compatible host.
    configured = os.getenv("DATABASE_PATH")
    if configured:
        return configured
    if os.getenv("VERCEL") == "1":
        # Vercel functions can write to /tmp, but it is ephemeral and not shared reliably.
        return "/tmp/musclemind.db"
    return str(Path(__file__).resolve().parent / "musclemind.db")


def connect_db():
    conn = sqlite3.connect(database_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = connect_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                google_id TEXT UNIQUE,
                profile_pic TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight REAL,
                waist REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()
