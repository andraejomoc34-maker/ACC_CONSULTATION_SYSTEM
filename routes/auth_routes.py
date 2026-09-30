from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        student_id = request.form.get("student_id", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        course = request.form.get("course", "").strip()
        year_level = request.form.get("year_level", "").strip()
        contact_number = request.form.get("contact_number", "").strip()
        address = request.form.get("address", "").strip()

        # Required fields
        if not full_name or not email or not password or not confirm_password:
            flash("Please complete all required fields.", "danger")
            return render_template("register.html")

        # Password confirmation
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        # Password length
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")

        connection = get_db_connection()

        existing_user = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            connection.close()
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        try:
            cursor = connection.execute(
                """
                INSERT INTO users
                (full_name, email, password, role, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    hashed_password,
                    "student",
                    "active"
                )
            )

            user_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO student_profiles
                (
                    user_id,
                    student_id,
                    age,
                    gender,
                    course,
                    year_level,
                    contact_number,
                    address
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    student_id,
                    age if age else None,
                    gender,
                    course,
                    year_level,
                    contact_number,
                    address
                )
            )

            connection.execute(
                """
                INSERT INTO activity_logs
                (user_id, action, description)
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    "REGISTER",
                    "Student account registered."
                )
            )

            connection.commit()
            connection.close()

            flash("Registration successful. You can now log in.", "success")

            return redirect(url_for("auth.login"))

        except Exception as error:

            connection.rollback()
            connection.close()

            print("Registration error:", error)

            flash(
                "Registration failed. Please try again.",
                "danger"
            )

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return render_template("login.html")

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if not user:

            connection.close()

            flash("Invalid email or password.", "danger")

            return render_template("login.html")

        if not check_password_hash(user["password"], password):

            connection.close()

            flash("Invalid email or password.", "danger")

            return render_template("login.html")

        if user["status"] != "active":

            connection.close()

            flash(
                "Your account is inactive. Please contact the administrator.",
                "danger"
            )

            return render_template("login.html")

        session.clear()

        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        connection.execute(
            """
            INSERT INTO activity_logs
            (user_id, action, description)
            VALUES (?, ?, ?)
            """,
            (
                user["id"],
                "LOGIN",
                "User logged into the system."
            )
        )

        connection.commit()
        connection.close()

        if user["role"] == "super_admin":
            return redirect(url_for("admin.dashboard"))

        elif user["role"] == "medical_expert":
            return redirect(url_for("expert.dashboard"))

        elif user["role"] == "student":
            return redirect(url_for("student.dashboard"))

        session.clear()

        flash("Invalid user role.", "danger")

    return render_template("login.html")


@auth.route("/logout")
def logout():

    user_id = session.get("user_id")

    if user_id:

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO activity_logs
            (user_id, action, description)
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                "LOGOUT",
                "User logged out of the system."
            )
        )

        connection.commit()
        connection.close()

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))