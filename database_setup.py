import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# IMPORTANT: Enable foreign keys in SQLite
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
    reg_number TEXT UNIQUE NOT NULL,
    email TEXT
)
""")


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