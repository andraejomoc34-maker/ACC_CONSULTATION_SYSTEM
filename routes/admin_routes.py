from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort
)

from werkzeug.security import generate_password_hash

from database import get_db_connection
from utils.decorators import role_required


admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


@admin.route("/dashboard")
@role_required("super_admin")
def dashboard():

    connection = get_db_connection()

    total_users = connection.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    total_students = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'student'
        """
    ).fetchone()["count"]

    total_experts = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'medical_expert'
        """
    ).fetchone()["count"]

    total_admins = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'super_admin'
        """
    ).fetchone()["count"]

    total_consultations = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        """
    ).fetchone()["count"]

    pending_consultations = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE status = 'Pending'
        """
    ).fetchone()["count"]

    in_review = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE status = 'In Review'
        """
    ).fetchone()["count"]

    completed = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE status = 'Completed'
        """
    ).fetchone()["count"]

    recent_users = connection.execute(
        """
        SELECT *
        FROM users
        ORDER BY created_at DESC
        LIMIT 5
        """
    ).fetchall()

    recent_consultations = connection.execute(
        """
        SELECT
            c.*,
            student.full_name AS student_name,
            expert.full_name AS expert_name
        FROM consultations c
        JOIN users student
            ON c.student_id = student.id
        LEFT JOIN users expert
            ON c.medical_expert_id = expert.id
        ORDER BY c.created_at DESC
        LIMIT 5
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_students=total_students,
        total_experts=total_experts,
        total_admins=total_admins,
        total_consultations=total_consultations,
        pending_consultations=pending_consultations,
        in_review=in_review,
        completed=completed,
        recent_users=recent_users,
        recent_consultations=recent_consultations
    )


@admin.route("/users")
@role_required("super_admin")
def users():

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()

    if search:

        users = connection.execute(
            """
            SELECT *
            FROM users
            WHERE
                full_name LIKE ?
                OR email LIKE ?
                OR role LIKE ?
            ORDER BY created_at DESC
            """,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            )
        ).fetchall()

    else:

        users = connection.execute(
            """
            SELECT *
            FROM users
            ORDER BY created_at DESC
            """
        ).fetchall()

    connection.close()

    return render_template(
        "admin/users.html",
        users=users,
        search=search
    )


@admin.route("/users/create", methods=["GET", "POST"])
@role_required("super_admin")
def create_user():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            ""
        )

        if not full_name or not email or not password or not role:

            flash(
                "Please complete all required fields.",
                "danger"
            )

            return render_template(
                "admin/create_user.html"
            )

        allowed_roles = [
            "student",
            "medical_expert",
            "super_admin"
        ]

        if role not in allowed_roles:

            flash(
                "Invalid role selected.",
                "danger"
            )

            return render_template(
                "admin/create_user.html"
            )

        connection = get_db_connection()

        existing = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing:

            connection.close()

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "admin/create_user.html"
            )

        password_hash = generate_password_hash(
            password
        )

        connection.execute(
            """
            INSERT INTO users
            (
                full_name,
                email,
                password,
                role,
                status
            )
            VALUES (?, ?, ?, ?, 'Active')
            """,
            (
                full_name,
                email,
                password_hash,
                role
            )
        )

        connection.execute(
            """
            INSERT INTO activity_logs
            (
                user_id,
                action,
                description
            )
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                "CREATE_USER",
                f"Created user account for {email}"
            )
        )

        connection.commit()
        connection.close()

        flash(
            "User account created successfully.",
            "success"
        )

        return redirect(
            url_for("admin.users")
        )

    return render_template(
        "admin/create_user.html"
    )


@admin.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@role_required("super_admin")
def edit_user(user_id):

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:

        connection.close()

        abort(404)

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        role = request.form.get(
            "role",
            ""
        )

        status = request.form.get(
            "status",
            ""
        )

        allowed_roles = [
            "student",
            "medical_expert",
            "super_admin"
        ]

        allowed_statuses = [
            "Active",
            "Inactive"
        ]

        if role not in allowed_roles:

            connection.close()

            flash(
                "Invalid role.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_user",
                    user_id=user_id
                )
            )

        if status not in allowed_statuses:

            connection.close()

            flash(
                "Invalid account status.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.edit_user",
                    user_id=user_id
                )
            )

        connection.execute(
            """
            UPDATE users

            SET
                full_name = ?,
                email = ?,
                role = ?,
                status = ?

            WHERE id = ?
            """,
            (
                full_name,
                email,
                role,
                status,
                user_id
            )
        )

        connection.execute(
            """
            INSERT INTO activity_logs
            (
                user_id,
                action,
                description
            )
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                "UPDATE_USER",
                f"Updated user #{user_id}"
            )
        )

        connection.commit()
        connection.close()

        flash(
            "User updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin.users")
        )

    connection.close()

    return render_template(
        "admin/edit_user.html",
        user=user
    )


@admin.route(
    "/users/<int:user_id>/toggle-status",
    methods=["POST"]
)
@role_required("super_admin")
def toggle_user_status(user_id):

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:

        connection.close()

        abort(404)

    if user["id"] == session["user_id"]:

        connection.close()

        flash(
            "You cannot deactivate your own account.",
            "danger"
        )

        return redirect(
            url_for("admin.users")
        )

    new_status = (
        "Inactive"
        if user["status"] == "Active"
        else "Active"
    )

    connection.execute(
        """
        UPDATE users
        SET status = ?
        WHERE id = ?
        """,
        (
            new_status,
            user_id
        )
    )

    connection.execute(
        """
        INSERT INTO activity_logs
        (
            user_id,
            action,
            description
        )
        VALUES (?, ?, ?)
        """,
        (
            session["user_id"],
            "TOGGLE_USER_STATUS",
            f"Changed user #{user_id} status to {new_status}"
        )
    )

    connection.commit()
    connection.close()

    flash(
        f"User status changed to {new_status}.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )


@admin.route("/consultations")
@role_required("super_admin")
def consultations():

    connection = get_db_connection()

    consultations = connection.execute(
        """
        SELECT
            c.*,
            student.full_name AS student_name,
            expert.full_name AS expert_name
        FROM consultations c

        JOIN users student
            ON c.student_id = student.id

        LEFT JOIN users expert
            ON c.medical_expert_id = expert.id

        ORDER BY c.created_at DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin/consultations.html",
        consultations=consultations
    )


@admin.route(
    "/consultations/<int:consultation_id>"
)
@role_required("super_admin")
def consultation_detail(consultation_id):

    connection = get_db_connection()

    consultation = connection.execute(
        """
        SELECT
            c.*,
            student.full_name AS student_name,
            student.email AS student_email,
            expert.full_name AS expert_name
        FROM consultations c

        JOIN users student
            ON c.student_id = student.id

        LEFT JOIN users expert
            ON c.medical_expert_id = expert.id

        WHERE c.id = ?
        """,
        (consultation_id,)
    ).fetchone()

    connection.close()

    if not consultation:
        abort(404)

    return render_template(
        "admin/consultation_detail.html",
        consultation=consultation
    )


@admin.route("/activity-logs")
@role_required("super_admin")
def activity_logs():

    connection = get_db_connection()

    logs = connection.execute(
        """
        SELECT
            logs.*,
            users.full_name,
            users.email
        FROM activity_logs logs

        LEFT JOIN users
            ON logs.user_id = users.id

        ORDER BY logs.created_at DESC
        LIMIT 200
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin/activity_logs.html",
        logs=logs
    )