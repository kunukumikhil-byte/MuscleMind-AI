import sqlite3

DATABASE = "musclemind.db"


def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weight REAL,
        waist REAL,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()