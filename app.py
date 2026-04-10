from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# LOAD ENV VARIABLES
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key")

# DATABASE CONNECTION
def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# EMAIL FUNCTION
def send_email(parent_email, student_name):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    subject = "Student Attendance Notification"
    body = f"Hello Parent,\n\nYour child {student_name} has arrived in class today."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = parent_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, parent_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Email failed: {e}")

# LOGIN PAGE
@app.route("/")
def login():
    return render_template("login.html")

# LOGIN USER
@app.route("/login", methods=["POST"])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["username"] = username
        return redirect("/dashboard")
    else:
        return "Invalid login"

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# REGISTER STUDENT PAGE
@app.route("/register")
def register_student():
    if "username" not in session:
        return redirect("/")
    return render_template("register_student.html")

# ADD STUDENT
@app.route("/add_student", methods=["POST"])
def add_student():
    if "username" not in session:
        return redirect("/")

    name = request.form.get("name")
    reg_number = request.form.get("reg_number")
    email = request.form.get("email")

    if not name or not reg_number:
        return "Name and Registration Number are required."

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students(name, reg_number, email) VALUES(?,?,?)",
            (name, reg_number, email)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return f"Database Error: {e}"
    conn.close()

    return redirect("/dashboard")

# VIEW STUDENTS
@app.route("/students")
def view_students():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    return render_template("students.html", students=students)

# ATTENDANCE PAGE
@app.route("/attendance")
def attendance():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    return render_template("mark_attendance.html", students=students)

# MARK ATTENDANCE (CLEAN VERSION)
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "username" not in session:
        return redirect("/")

    student_id = request.form.get("student_id")

    if not student_id:
        return "Student not selected"

    date = datetime.date.today().isoformat()
    time = datetime.datetime.now().strftime("%H:%M:%S")

    conn = connect_db()
    cursor = conn.cursor()

    # PREVENT DUPLICATE ATTENDANCE
    cursor.execute(
        "SELECT * FROM attendance WHERE student_id=? AND date=?",
        (student_id, date)
    )
    if cursor.fetchone():
        conn.close()
        return "Attendance already marked today"

    try:
        cursor.execute(
            "INSERT INTO attendance(student_id, date, time) VALUES(?,?,?)",
            (student_id, date, time)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return f"Database Error: {e}"

    cursor.execute("SELECT name, email FROM students WHERE id=?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    # SEND EMAIL
    if student and student["email"]:
        send_email(student["email"], student["name"])

    return redirect("/dashboard")

# ATTENDANCE REPORT
@app.route("/attendance_report")
def attendance_report():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT students.name, students.reg_number, attendance.date, attendance.time
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """)
    records = cursor.fetchall()
    conn.close()

    return render_template("attendance_report.html", records=records)

# REGISTER USER PAGE
@app.route("/register_user")
def register_user():
    if "username" not in session:
        return redirect("/")
    return render_template("register_user.html")

# ADD USER (WITH HASHED PASSWORD)
@app.route("/add_user", methods=["POST"])
def add_user():
    if "username" not in session:
        return redirect("/")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return "Username and Password are required."

    hashed_password = generate_password_hash(password)

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return f"Database Error: {e}"
    conn.close()

    return redirect("/dashboard")

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)