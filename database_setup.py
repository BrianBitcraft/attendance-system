import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# ---------------- USERS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# ---------------- STUDENTS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    reg_number TEXT UNIQUE NOT NULL
)
""")

# 🔥 FIX: ADD EMAIL COLUMN IF IT DOES NOT EXIST
try:
    cursor.execute("ALTER TABLE students ADD COLUMN email TEXT")
    print("✅ email column added to students table")
except sqlite3.OperationalError:
    print("ℹ️ email column already exists")

# ---------------- ATTENDANCE TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(id)
        ON DELETE CASCADE
)
""")

# ---------------- DEFAULT ADMIN ----------------
cursor.execute("""
INSERT OR IGNORE INTO users (username, password)
VALUES (?, ?)
""", ("admin", "1234"))

conn.commit()
conn.close()

print("✅ Database created successfully!")