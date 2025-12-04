import sqlite3

def get_db(path="bot_data.db"):
    conn = sqlite3.connect(path)
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
