from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# -------------------- LOAD ENV VARIABLES --------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# -------------------- DATABASE CONNECTION --------------------
def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- EMAIL FUNCTION --------------------
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
        print(f"Email sent to {parent_email}")

    except Exception as e:
        print(f"Email failed: {e}")

# -------------------- LOGIN --------------------
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["username"] = username
        return redirect("/dashboard")
    else:
        return "Invalid login"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# -------------------- REGISTER STUDENT --------------------
@app.route("/register")
def register_student():
    if "username" not in session:
        return redirect("/")
    return render_template("register_student.html")

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

# -------------------- VIEW STUDENTS --------------------
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

# -------------------- ATTENDANCE PAGE --------------------
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

# -------------------- MARK ATTENDANCE --------------------
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "username" not in session:
        return redirect("/")

    # Only allow mobile users
    user_agent = request.headers.get("User-Agent", "")
    if not any(x in user_agent for x in ["iPhone", "iPad", "iPod", "Android"]):
        return "Attendance marking only works on smartphones with fingerprint scanner."

    student_id = request.form.get("student_id")
    if not student_id:
        return "Student not selected"

    date = datetime.date.today().isoformat()
    time = datetime.datetime.now().strftime("%H:%M:%S")

    conn = connect_db()
    cursor = conn.cursor()
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

    if student:
        student_name = student["name"]
        parent_email = student["email"]
        if parent_email:
            try:
                send_email(parent_email, student_name)
            except Exception as e:
                print(f"Email sending error: {e}")

    return redirect("/dashboard")

# -------------------- ATTENDANCE REPORT --------------------
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

# -------------------- REGISTER USER --------------------
@app.route("/register_user")
def register_user():
    if "username" not in session:
        return redirect("/")
    return render_template("register_user.html")

@app.route("/add_user", methods=["POST"])
def add_user():
    if "username" not in session:
        return redirect("/")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return "Username and Password are required."

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users(username,password) VALUES(?,?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return f"Database Error: {e}"
    conn.close()

    return redirect("/dashboard")

# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)