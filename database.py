import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Donor table with new lat/lng
cur.execute("""
CREATE TABLE IF NOT EXISTS donor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    blood_group TEXT,
    phone TEXT,
    city TEXT,
    last_donated DATE,
    available INTEGER,
    lat REAL,
    lng REAL
)
""")

cur.execute("ALTER TABLE donor ADD COLUMN email TEXT")

# Users table for authentication
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Emergency table
cur.execute("""
CREATE TABLE IF NOT EXISTS emergency (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    blood_group TEXT,
    city TEXT,
    contact TEXT,
    date TEXT
)
""")

conn.commit()
conn.close()
print("Database updated successfully")