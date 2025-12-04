# database.py

import sqlite3
from config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sudos(
            user_id INTEGER PRIMARY KEY
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_admins(
            user_id INTEGER PRIMARY KEY
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS directory(
            chat_id INTEGER PRIMARY KEY,
            chat_type TEXT,
            link TEXT,
            title TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS banned_global(
            user_id INTEGER PRIMARY KEY,
            reason TEXT
        );
    """)

    db.commit()
    db.close()

# ---------- Sudo ----------
def add_sudo(uid):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO sudos (user_id) VALUES (?)", (uid,))
    db.commit()
    db.close()

def rm_sudo(uid):
    db = get_db()
    db.execute("DELETE FROM sudos WHERE user_id = ?", (uid,))
    db.commit()
    db.close()

def get_sudos():
    db = get_db()
    rows = db.execute("SELECT user_id FROM sudos").fetchall()
    db.close()
    return [r["user_id"] for r in rows]

# ---------- Global Admin ----------
def add_global_admin(uid):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO global_admins (user_id) VALUES (?)", (uid,))
    db.commit()
    db.close()

def rm_global_admin(uid):
    db = get_db()
    db.execute("DELETE FROM global_admins WHERE user_id = ?", (uid,))
    db.commit()
    db.close()

def get_global_admins():
    db = get_db()
    rows = db.execute("SELECT user_id FROM global_admins").fetchall()
    db.close()
    return [r["user_id"] for r in rows]

# ---------- Directory ----------
def add_directory(cid, ctype, link, title=""):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO directory (chat_id, chat_type, link, title)
        VALUES (?, ?, ?, ?)
    """, (cid, ctype, link, title))
    db.commit()
    db.close()

def rm_directory(cid):
    db = get_db()
    db.execute("DELETE FROM directory WHERE chat_id = ?", (cid,))
    db.commit()
    db.close()

def get_directory():
    db = get_db()
    rows = db.execute("SELECT * FROM directory").fetchall()
    db.close()
    return rows

# ---------- Global Bans ----------
def add_global_ban(uid, reason=""):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO banned_global (user_id, reason) VALUES (?, ?)", (uid, reason))
    db.commit()
    db.close()

def rm_global_ban(uid):
    db = get_db()
    db.execute("DELETE FROM banned_global WHERE user_id = ?", (uid,))
    db.commit()
    db.close()

def get_global_bans():
    db = get_db()
    rows = db.execute("SELECT user_id FROM banned_global").fetchall()
    db.close()
    return [r["user_id"] for r in rows]
