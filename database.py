import sqlite3

DATABASE = "musclemind.db"


def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # ---------------- USERS TABLE ---------------- #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        google_id TEXT UNIQUE,
        profile_pic TEXT
    )
    """)

    # ---------------- PROGRESS TABLE ---------------- #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        weight REAL,
        waist REAL,
        notes TEXT,

        FOREIGN KEY (user_id)
        REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()