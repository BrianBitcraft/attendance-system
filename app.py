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
    return sqlite3.connect("database.db")


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
        print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)


# -------------------- LOGIN --------------------
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    username = request.form["username"]
    password = request.form["password"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

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

    name = request.form["name"]
    reg_number = request.form["reg_number"]
    email = request.form["email"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO students(name, reg_number, email) VALUES(?,?,?)",
        (name, reg_number, email)
    )

    conn.commit()
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

    return render_template("attendance.html", students=students)


# -------------------- MARK ATTENDANCE --------------------
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():

    if "username" not in session:
        return redirect("/")

    student_id = request.form["student_id"]

    date = datetime.date.today()
    time = datetime.datetime.now().strftime("%H:%M:%S")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO attendance(student_id, date, time) VALUES(?,?,?)",
        (student_id, date, time)
    )

    conn.commit()

    cursor.execute(
        "SELECT name, email FROM students WHERE id=?",
        (student_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:

        student_name = result[0]
        parent_email = result[1]

        if parent_email:
            send_email(parent_email, student_name)

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

    username = request.form["username"]
    password = request.form["password"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        (username, password)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)