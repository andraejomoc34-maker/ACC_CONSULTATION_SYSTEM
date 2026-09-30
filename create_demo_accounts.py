from database import get_db_connection, init_db

from werkzeug.security import generate_password_hash


def create_user(
    full_name,
    email,
    password,
    role
):

    connection = get_db_connection()

    existing = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:

        print(f"{email} already exists.")

        connection.close()

        return

    hashed_password = generate_password_hash(password)

    cursor = connection.execute(
        """
        INSERT INTO users
        (
            full_name,
            email,
            password,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            full_name,
            email,
            hashed_password,
            role,
            "active"
        )
    )

    user_id = cursor.lastrowid

    if role == "medical_expert":

        connection.execute(
            """
            INSERT INTO medical_expert_profiles
            (
                user_id,
                specialization,
                license_number,
                contact_number
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                "General Medicine",
                "DEMO-LICENSE-001",
                "09123456789"
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
            "CREATE_USER",
            f"Development {role} account created."
        )
    )

    connection.commit()

    connection.close()

    print(f"Created {role}: {email}")


init_db()


create_user(
    "System Administrator",
    "admin@example.com",
    "Admin@12345",
    "super_admin"
)


create_user(
    "Dr. Demo Expert",
    "expert@example.com",
    "Expert@12345",
    "medical_expert"
)


print()
print("Demo accounts are ready.")