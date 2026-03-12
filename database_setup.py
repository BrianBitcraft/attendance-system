import sqlite3

# Connect to database (creates database.db if it doesn't exist)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ==========================
# CREATE TABLES
# ==========================

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

# STUDENTS TABLE (with parent email)
cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    reg_number TEXT,
    email TEXT
)
""")

# ATTENDANCE TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    time TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

# ==========================
# DEFAULT DATA
# ==========================

# Insert default lecturer/admin login (if not exists)
cursor.execute("""
INSERT OR IGNORE INTO users(username, password)
VALUES('admin','1234')
""")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database created successfully!")