import sqlite3
import uuid
from datetime import datetime, timedelta

DB_FILE = "payments.db"

# ===============================
# CONFIGURABLE SETTINGS
# ===============================
MAX_CONCURRENT_USERS = 3
SESSION_TIMEOUT_MINUTES = 30


# ===============================
# INIT DB
# ===============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            order_id TEXT,
            access_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT,
            session_id TEXT UNIQUE,
            last_active TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Run init automatically on import
init_db()


# ===============================
# SAVE PAYMENT + GENERATE TOKEN
# ===============================
def save_payment(email, order_id):
    token = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO payments (email, order_id, access_token) VALUES (?, ?, ?)",
        (email, order_id, token)
    )

    conn.commit()
    conn.close()

    return token


# ===============================
# CLEAN EXPIRED SESSIONS
# ===============================
def cleanup_expired_sessions(cursor):
    expiry_time = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    cursor.execute(
        "DELETE FROM active_sessions WHERE last_active < ?",
        (expiry_time.isoformat(),)
    )


# ===============================
# VERIFY TOKEN + MANAGE SESSION
# ===============================
def verify_and_register_session(token, session_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check token exists
    cursor.execute(
        "SELECT id FROM payments WHERE access_token=?",
        (token,)
    )
    if not cursor.fetchone():
        conn.close()
        return False, "Invalid token"

    # Cleanup old sessions
    cleanup_expired_sessions(cursor)

    # Check if session already active
    cursor.execute(
        "SELECT id FROM active_sessions WHERE session_id=?",
        (session_id,)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE active_sessions SET last_active=? WHERE session_id=?",
            (datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
        conn.close()
        return True, "Session refreshed"

    # Count active users for this token
    cursor.execute(
        "SELECT COUNT(*) FROM active_sessions WHERE access_token=?",
        (token,)
    )
    active_count = cursor.fetchone()[0]

    if active_count >= MAX_CONCURRENT_USERS:
        conn.close()
        return False, "Max users reached"

    # Register new session
    cursor.execute(
        "INSERT INTO active_sessions (access_token, session_id, last_active) VALUES (?, ?, ?)",
        (token, session_id, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()

    return True, "Session registered"
