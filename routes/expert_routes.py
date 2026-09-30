from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort

from database import get_db_connection
from utils.decorators import role_required


expert = Blueprint(
    "expert",
    __name__,
    url_prefix="/expert"
)


@expert.route("/dashboard")
@role_required("medical_expert")
def dashboard():

    connection = get_db_connection()

    total = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE medical_expert_id = ?
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    pending = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE medical_expert_id = ?
        AND status = 'Pending'
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    in_review = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE medical_expert_id = ?
        AND status = 'In Review'
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    completed = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM consultations
        WHERE medical_expert_id = ?
        AND status = 'Completed'
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    recent = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS student_name
        FROM consultations c
        JOIN users u
            ON c.student_id = u.id
        WHERE c.medical_expert_id = ?
        ORDER BY c.created_at DESC
        LIMIT 5
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "expert/dashboard.html",
        total=total,
        pending=pending,
        in_review=in_review,
        completed=completed,
        recent=recent
    )


@expert.route("/consultations")
@role_required("medical_expert")
def consultations():

    connection = get_db_connection()

    consultations = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS student_name,
            u.email AS student_email
        FROM consultations c
        JOIN users u
            ON c.student_id = u.id
        WHERE c.medical_expert_id = ?
        ORDER BY c.created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "expert/consultations.html",
        consultations=consultations
    )


@expert.route("/consultations/<int:consultation_id>")
@role_required("medical_expert")
def consultation_detail(consultation_id):

    connection = get_db_connection()

    consultation = connection.execute(
        """
        SELECT
            c.*,
            u.full_name AS student_name,
            u.email AS student_email
        FROM consultations c
        JOIN users u
            ON c.student_id = u.id
        WHERE c.id = ?
        AND c.medical_expert_id = ?
        """,
        (
            consultation_id,
            session["user_id"]
        )
    ).fetchone()

    connection.close()

    if not consultation:
        abort(404)

    return render_template(
        "expert/consultation_detail.html",
        consultation=consultation
    )


@expert.route(
    "/consultations/<int:consultation_id>/accept",
    methods=["POST"]
)
@role_required("medical_expert")
def accept_consultation(consultation_id):

    connection = get_db_connection()

    consultation = connection.execute(
        """
        SELECT *
        FROM consultations
        WHERE id = ?
        AND medical_expert_id = ?
        """,
        (
            consultation_id,
            session["user_id"]
        )
    ).fetchone()

    if not consultation:
        connection.close()
        abort(404)

    connection.execute(
        """
        UPDATE consultations
        SET status = 'In Review'
        WHERE id = ?
        """,
        (consultation_id,)
    )

    connection.commit()
    connection.close()

    flash(
        "Consultation accepted.",
        "success"
    )

    return redirect(
        url_for(
            "expert.consultation_detail",
            consultation_id=consultation_id
        )
    )


@expert.route(
    "/consultations/<int:consultation_id>/respond",
    methods=["POST"]
)
@role_required("medical_expert")
def respond_consultation(consultation_id):

    response = request.form.get(
        "expert_response",
        ""
    ).strip()

    if not response:

        flash(
            "Please enter a response.",
            "danger"
        )

        return redirect(
            url_for(
                "expert.consultation_detail",
                consultation_id=consultation_id
            )
        )

    connection = get_db_connection()

    consultation = connection.execute(
        """
        SELECT *
        FROM consultations
        WHERE id = ?
        AND medical_expert_id = ?
        """,
        (
            consultation_id,
            session["user_id"]
        )
    ).fetchone()

    if not consultation:
        connection.close()
        abort(404)

    connection.execute(
        """
        UPDATE consultations

        SET
            expert_response = ?,
            status = 'Responded'

        WHERE id = ?
        """,
        (
            response,
            consultation_id
        )
    )

    connection.commit()
    connection.close()

    flash(
        "Response submitted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "expert.consultation_detail",
            consultation_id=consultation_id
        )
    )


@expert.route(
    "/consultations/<int:consultation_id>/complete",
    methods=["POST"]
)
@role_required("medical_expert")
def complete_consultation(consultation_id):

    connection = get_db_connection()

    consultation = connection.execute(
        """
        SELECT *
        FROM consultations
        WHERE id = ?
        AND medical_expert_id = ?
        """,
        (
            consultation_id,
            session["user_id"]
        )
    ).fetchone()

    if not consultation:
        connection.close()
        abort(404)

    connection.execute(
        """
        UPDATE consultations
        SET status = 'Completed'
        WHERE id = ?
        """,
        (consultation_id,)
    )

    connection.commit()
    connection.close()

    flash(
        "Consultation marked as completed.",
        "success"
    )

    return redirect(
        url_for(
            "expert.consultation_detail",
            consultation_id=consultation_id
        )
    )