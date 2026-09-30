import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "acc_consultation.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (
                role IN ('super_admin', 'medical_expert', 'student')
            ),
            status TEXT NOT NULL DEFAULT 'active' CHECK (
                status IN ('active', 'inactive')
            ),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            student_id TEXT NOT NULL UNIQUE,
            age INTEGER,
            gender TEXT,
            course TEXT,
            year_level TEXT,
            contact_number TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS medical_expert_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            specialization TEXT,
            license_number TEXT,
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            medical_expert_id INTEGER,
            consultation_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            concern TEXT NOT NULL,
            additional_information TEXT,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK (
                status IN (
                    'Pending',
                    'In Review',
                    'Responded',
                    'Completed',
                    'Cancelled'
                )
            ),
            expert_response TEXT,
            expert_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (medical_expert_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_users_email
        ON users(email);

        CREATE INDEX IF NOT EXISTS idx_users_role
        ON users(role);

        CREATE INDEX IF NOT EXISTS idx_consultations_student
        ON consultations(student_id);

        CREATE INDEX IF NOT EXISTS idx_consultations_expert
        ON consultations(medical_expert_id);

        CREATE INDEX IF NOT EXISTS idx_consultations_status
        ON consultations(status);

        CREATE INDEX IF NOT EXISTS idx_activity_logs_user
        ON activity_logs(user_id);
    """)

    connection.commit()
    connection.close()

    print("Database initialized successfully.")