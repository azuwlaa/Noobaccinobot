import sqlite3

DB_PATH = "bot_data.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
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


# -------------------------
# SUDO FUNCTIONS
# -------------------------
def add_sudo(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR IGNORE INTO sudos (user_id) VALUES (?)", (user_id,))
    db.commit()
    db.close()

def rm_sudo(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM sudos WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()

def get_sudos():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM sudos")
    rows = cur.fetchall()
    db.close()
    return [r[0] for r in rows]


# -------------------------
# GLOBAL ADMINS
# -------------------------
def add_global_admin(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT OR IGNORE INTO global_admins (user_id) VALUES (?)", (user_id,))
    db.commit()
    db.close()

def rm_global_admin(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM global_admins WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()

def get_global_admins():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM global_admins")
    rows = cur.fetchall()
    db.close()
    return [r[0] for r in rows]


# -------------------------
# DIRECTORY
# -------------------------
def add_directory(chat_id: int, chat_type: str, link: str, title: str = ""):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO directory (chat_id, chat_type, link, title)
        VALUES (?, ?, ?, ?)
    """, (chat_id, chat_type, link, title))
    db.commit()
    db.close()

def rm_directory(chat_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM directory WHERE chat_id = ?", (chat_id,))
    db.commit()
    db.close()

def get_directory():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM directory")
    rows = cur.fetchall()
    db.close()
    return rows


# -------------------------
# GLOBAL BAN
# -------------------------
def add_global_ban(user_id: int, reason: str = ""):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO banned_global (user_id, reason)
        VALUES (?, ?)
    """, (user_id, reason))
    db.commit()
    db.close()

def rm_global_ban(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM banned_global WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()

def get_global_bans():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT user_id FROM banned_global")
    rows = cur.fetchall()
    db.close()
    return [r[0] for r in rows]
