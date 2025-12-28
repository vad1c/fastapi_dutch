import sqlite3

DB = "cards.db"

def col_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == col for row in cur.fetchall())

conn = sqlite3.connect(DB)
cur = conn.cursor()

if not col_exists(cur, "cards", "ru"):
    cur.execute("ALTER TABLE cards ADD COLUMN ru TEXT;")
    print("✅ added ru")
else:
    print("ℹ️ ru already exists")

if not col_exists(cur, "cards", "ukr"):
    cur.execute("ALTER TABLE cards ADD COLUMN ukr TEXT;")
    print("✅ added ukr")
else:
    print("ℹ️ ukr already exists")

conn.commit()
conn.close()
print("✅ migration done")
