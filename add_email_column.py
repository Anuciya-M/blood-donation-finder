import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE donor ADD COLUMN email TEXT")
    conn.commit()
    print("Column 'email' added successfully to donor table!")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e):
        print("Column 'email' already exists. No changes needed.")
    else:
        raise e

conn.close()