from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort

from database import get_db_connection
from utils.decorators import role_required


student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


@student.route("/dashboard")
@role_required("student")
def dashboard():

    user_id = session["user_id"]

    connection = get_db_connection()

    total = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE student_id = ?
        """,
        (user_id,)
    ).fetchone()["count"]

    pending = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE student_id = ?
        AND status = 'Pending'
        """,
        (user_id,)
    ).fetchone()["count"]

    in_review = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE student_id = ?
        AND status = 'In Review'
        """,
        (user_id,)
    ).fetchone()["count"]

    responded = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE student_id = ?
        AND status = 'Responded'
        """,
        (user_id,)
    ).fetchone()["count"]

    completed = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE student_id = ?
        AND status = 'Completed'
        """,
        (user_id,)
    ).fetchone()["count"]

    recent_consultations = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS expert_name
        FROM consultations c
        LEFT JOIN users u
            ON c.medical_expert_id = u.id
        WHERE c.student_id = ?
        ORDER BY c.created_at DESC
        LIMIT 5
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "student/dashboard.html",
        total=total,
        pending=pending,
        in_review=in_review,
        responded=responded,
        completed=completed,
        recent_consultations=recent_consultations
    )


@student.route("/consultations")
@role_required("student")
def consultations():

    user_id = session["user_id"]

    connection = get_db_connection()

    consultations = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS expert_name
        FROM consultations c
        LEFT JOIN users u
            ON c.medical_expert_id = u.id
        WHERE c.student_id = ?
        ORDER BY c.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "student/consultations.html",
        consultations=consultations
    )


@student.route("/consultations/create", methods=["GET", "POST"])
@role_required("student")
def create_consultation():

    if request.method == "POST":

        consultation_type = request.form.get(
            "consultation_type",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        concern = request.form.get(
            "concern",
            ""
        ).strip()

        additional_information = request.form.get(
            "additional_information",
            ""
        ).strip()

        if not consultation_type:
            flash(
                "Please select a consultation type.",
                "danger"
            )

            return render_template(
                "student/create_consultation.html"
            )

        if not subject:
            flash(
                "Please enter a subject.",
                "danger"
            )

            return render_template(
                "student/create_consultation.html"
            )

        if not concern:
            flash(
                "Please describe your concern.",
                "danger"
            )

            return render_template(
                "student/create_consultation.html"
            )

        user_id = session["user_id"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO consultations
            (
                student_id,
                medical_expert_id,
                consultation_type,
                subject,
                concern,
                additional_information,
                status
            )
            VALUES (?, NULL, ?, ?, ?, ?, 'Pending')
            """,
            (
                user_id,
                consultation_type,
                subject,
                concern,
                additional_information
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
                user_id,
                "CREATE_CONSULTATION",
                f"Created consultation: {subject}"
            )
        )

        connection.commit()
        connection.close()

        flash(
            "Your consultation has been submitted successfully.",
            "success"
        )

        return redirect(
            url_for("student.consultations")
        )

    return render_template(
        "student/create_consultation.html"
    )


@student.route("/consultations/<int:consultation_id>")
@role_required("student")
def consultation_detail(consultation_id):

    user_id = session["user_id"]

    connection = get_db_connection()

    consultation = connection.execute(
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

        WHERE c.id = ?
        AND c.student_id = ?
        """,
        (
            consultation_id,
            user_id
        )
    ).fetchone()

    connection.close()

    if not consultation:
        abort(404)

    return render_template(
        "student/consultation_detail.html",
        consultation=consultation
    )


@student.route("/history")
@role_required("student")
def history():

    user_id = session["user_id"]

    connection = get_db_connection()

    consultations = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS expert_name
        FROM consultations c
        LEFT JOIN users u
            ON c.medical_expert_id = u.id
        WHERE c.student_id = ?
        AND c.status IN ('Responded', 'Completed')
        ORDER BY c.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "student/history.html",
        consultations=consultations
    )