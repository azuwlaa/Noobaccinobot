import sqlite3

DB = "bot.db"

# ---------------------------------------------------
# INIT
# ---------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS sudos (user_id INTEGER PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS global_admins (user_id INTEGER PRIMARY KEY)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS directory (
            chat_id INTEGER PRIMARY KEY,
            type TEXT,
            link TEXT,
            title TEXT
        )
    """)

    cur.execute("CREATE TABLE IF NOT EXISTS global_bans (user_id INTEGER PRIMARY KEY)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_cache (
            chat_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_titles (
            chat_id INTEGER,
            user_id INTEGER,
            title TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

    conn.commit()
    conn.close()

# ---------------------------------------------------
# SUDOS
# ---------------------------------------------------
def get_sudos():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    rows = cur.execute("SELECT user_id FROM sudos").fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_sudo(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sudos (user_id) VALUES (?)", (uid,))
    conn.commit()
    conn.close()

def rm_sudo(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM sudos WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

# ---------------------------------------------------
# GLOBAL ADMINS
# ---------------------------------------------------
def add_global_admin(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO global_admins (user_id) VALUES (?)", (uid,))
    conn.commit()
    conn.close()

def rm_global_admin(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM global_admins WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

# ---------------------------------------------------
# DIRECTORY
# ---------------------------------------------------
def add_directory(chat_id, t, link, title):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO directory (chat_id, type, link, title)
        VALUES (?, ?, ?, ?)
    """, (chat_id, t, link, title))
    conn.commit()
    conn.close()

def rm_directory(chat_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM directory WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def get_directory():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM directory").fetchall()
    conn.close()
    return rows

# ---------------------------------------------------
# GLOBAL BANS
# ---------------------------------------------------
def add_global_ban(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO global_bans (user_id) VALUES (?)", (uid,))
    conn.commit()
    conn.close()

def rm_global_ban(uid):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM global_bans WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

# ---------------------------------------------------
# ADMIN CACHE
# ---------------------------------------------------
def cache_admins(chat_id, user_ids):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("DELETE FROM admin_cache WHERE chat_id=?", (chat_id,))

    for uid in user_ids:
        cur.execute(
            "INSERT INTO admin_cache (chat_id, user_id) VALUES (?, ?)",
            (chat_id, uid)
        )

    conn.commit()
    conn.close()

# ---------------------------------------------------
# ADMIN TITLES
# ---------------------------------------------------
def save_admin_title(chat_id, user_id, title):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO admin_titles (chat_id, user_id, title)
        VALUES (?, ?, ?)
    """, (chat_id, user_id, title))
    conn.commit()
    conn.close()

def get_admin_title(chat_id, user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT title FROM admin_titles WHERE chat_id=? AND user_id=?",
        (chat_id, user_id)
    ).fetchone()
    conn.close()
    return row[0] if row else None
