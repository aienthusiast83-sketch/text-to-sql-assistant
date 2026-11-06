import sqlite3

conn = sqlite3.connect("Chinook_Sqlite.sqlite")
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for (t,) in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {count} rows")