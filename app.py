from flask import Flask, render_template, request, redirect, session
import sqlite3
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key")


# ---------------- DATABASE ----------------
def connect_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- EMAIL ----------------
def send_email(parent_email, student_name):
    try:
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")

        msg = MIMEText(f"Hello Parent,\n\n{student_name} has arrived in class today.")
        msg["Subject"] = "Attendance Notification"
        msg["From"] = sender_email
        msg["To"] = parent_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, parent_email, msg.as_string())
        server.quit()

    except Exception as e:
        print("Email error:", e)


# ---------------- LOGIN ----------------
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = connect_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["username"] = username
        return redirect("/dashboard")

    return "Invalid login"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html")


# ---------------- STUDENTS ----------------
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

    conn = connect_db()
    try:
        conn.execute(
            "INSERT INTO students(name, reg_number, email) VALUES(?,?,?)",
            (name, reg_number, email)
        )
        conn.commit()
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

    return redirect("/dashboard")


@app.route("/students")
def view_students():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("students.html", students=students)


# ---------------- ATTENDANCE ----------------
@app.route("/attendance")
def attendance():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("mark_attendance.html", students=students)


@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "username" not in session:
        return redirect("/")

    try:
        student_id = request.form.get("student_id")
        verified = request.form.get("verified")

        if not student_id:
            return "No student selected"

        if verified != "true":
            return "Fingerprint not verified"

        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().strftime("%H:%M:%S")

        conn = connect_db()

        existing = conn.execute(
            "SELECT 1 FROM attendance WHERE student_id=? AND date=?",
            (student_id, today)
        ).fetchone()

        if existing:
            conn.close()
            return "Already marked today"

        conn.execute(
            "INSERT INTO attendance(student_id, date, time) VALUES(?,?,?)",
            (student_id, today, now)
        )
        conn.commit()

        student = conn.execute(
            "SELECT name, email FROM students WHERE id=?",
            (student_id,)
        ).fetchone()

        conn.close()

        if student and student["email"]:
            send_email(student["email"], student["name"])

        return redirect("/dashboard")

    except Exception as e:
        return f"Server Error: {e}"


# ---------------- REPORT ----------------
@app.route("/attendance_report")
def attendance_report():
    if "username" not in session:
        return redirect("/")

    conn = connect_db()
    records = conn.execute("""
        SELECT students.name, students.reg_number, attendance.date, attendance.time
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """).fetchall()
    conn.close()

    return render_template("attendance_report.html", records=records)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)