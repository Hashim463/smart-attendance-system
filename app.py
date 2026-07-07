import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import query
from utils.face_utils import register_face_from_webcam, run_recognition_and_mark_attendance
from utils.excel_utils import export_attendance_to_excel

app = Flask(__name__)
app.config.from_object(Config)


# ---------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------
def login_required_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as admin.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def login_required_student(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("student_id"):
            flash("Please log in.", "error")
            return redirect(url_for("student_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        admin = query(
            "SELECT * FROM admins WHERE username = %s", (username,), fetchone=True
        )
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------
@app.route("/admin/dashboard")
@login_required_admin
def admin_dashboard():
    total_students = query("SELECT COUNT(*) AS c FROM students", fetchone=True)["c"]
    today = datetime.date.today()
    present_today = query(
        "SELECT COUNT(*) AS c FROM attendance WHERE date = %s", (today,), fetchone=True
    )["c"]
    recent = query(
        """
        SELECT s.name, s.roll_no, a.date, a.time_in, a.status
        FROM attendance a JOIN students s ON s.id = a.student_id
        ORDER BY a.date DESC, a.time_in DESC LIMIT 10
        """,
        fetch=True,
    )
    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        present_today=present_today,
        recent=recent,
    )


@app.route("/admin/students")
@login_required_admin
def admin_students():
    students = query("SELECT * FROM students ORDER BY name", fetch=True)
    return render_template("admin_students.html", students=students)


@app.route("/admin/students/add", methods=["GET", "POST"])
@login_required_admin
def admin_add_student():
    if request.method == "POST":
        roll_no = request.form["roll_no"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        class_section = request.form.get("class_section", "").strip()
        password = request.form["password"]

        existing = query(
            "SELECT id FROM students WHERE roll_no = %s OR email = %s",
            (roll_no, email),
            fetchone=True,
        )
        if existing:
            flash("A student with that roll number or email already exists.", "error")
            return redirect(url_for("admin_add_student"))

        password_hash = generate_password_hash(password)
        new_id = query(
            """
            INSERT INTO students (roll_no, name, email, password_hash, class_section)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (roll_no, name, email, password_hash, class_section),
            commit=True,
        )
        flash(f"Student '{name}' added. Now register their face.", "success")
        return redirect(url_for("admin_register_face", student_id=new_id))

    return render_template("admin_add_student.html")


@app.route("/admin/students/<int:student_id>/register_face")
@login_required_admin
def admin_register_face(student_id):
    """
    Triggers webcam-based face capture on the server machine.
    NOTE: this opens a local OpenCV window -- intended to be run on the
    admin/registration PC that has a physical camera attached, not a
    remote server.
    """
    student = query("SELECT * FROM students WHERE id = %s", (student_id,), fetchone=True)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for("admin_students"))

    success, message = register_face_from_webcam(student_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin_students"))


@app.route("/admin/recognize")
@login_required_admin
def admin_recognize():
    """
    Triggers webcam-based recognition + attendance marking.
    Opens a local OpenCV window; press 'q' inside it to stop.
    """
    result = run_recognition_and_mark_attendance()
    if "error" in result:
        flash(result["error"], "error")
    else:
        count = len(result["results"])
        flash(f"Recognition session complete. {count} student(s) marked present.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reports", methods=["GET", "POST"])
@login_required_admin
def admin_reports():
    date_from = request.values.get("date_from") or None
    date_to = request.values.get("date_to") or None

    sql = """
        SELECT s.roll_no, s.name, a.date, a.time_in, a.status
        FROM attendance a JOIN students s ON s.id = a.student_id
        WHERE 1=1
    """
    params = []
    if date_from:
        sql += " AND a.date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND a.date <= %s"
        params.append(date_to)
    sql += " ORDER BY a.date DESC, s.name ASC"

    records = query(sql, params, fetch=True)
    return render_template(
        "admin_reports.html", records=records, date_from=date_from, date_to=date_to
    )


@app.route("/admin/export")
@login_required_admin
def admin_export():
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    filepath = export_attendance_to_excel(date_from=date_from, date_to=date_to)
    return send_file(filepath, as_attachment=True)


# ---------------------------------------------------------------------
# Student auth + dashboard
# ---------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        student = query(
            "SELECT * FROM students WHERE email = %s", (email,), fetchone=True
        )
        if student and check_password_hash(student["password_hash"], password):
            session.clear()
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            return redirect(url_for("student_dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("student_login.html")


@app.route("/logout")
def student_logout():
    session.clear()
    return redirect(url_for("student_login"))


@app.route("/dashboard")
@login_required_student
def student_dashboard():
    student_id = session["student_id"]
    records = query(
        "SELECT date, time_in, status FROM attendance WHERE student_id = %s ORDER BY date DESC",
        (student_id,),
        fetch=True,
    )
    total_days = len(records)
    present_days = len([r for r in records if r["status"] in ("Present", "Late")])
    percentage = round((present_days / total_days) * 100, 1) if total_days else 0

    return render_template(
        "student_dashboard.html",
        records=records,
        percentage=percentage,
        total_days=total_days,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
