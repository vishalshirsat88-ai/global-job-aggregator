db.py 9th march

import psycopg2
import os
import uuid
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)


# ===============================
# CONFIGURABLE SETTINGS
# ===============================
MAX_CONCURRENT_USERS = 3
SESSION_TIMEOUT_MINUTES = 30


# ===============================
# INIT DB
# ===============================
def init_db():
    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            email TEXT,
            order_id TEXT,
            access_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions (
            id SERIAL PRIMARY KEY,
            access_token TEXT,
            session_id TEXT UNIQUE,
            last_active TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    
# ===============================
# SAVE PAYMENT + GENERATE TOKEN
# ===============================
def save_payment(email, order_id):
    token = str(uuid.uuid4()).strip()

    conn = get_db()
    cursor = conn.cursor()


    cursor.execute(
        "INSERT INTO payments (email, order_id, access_token) VALUES (%s, %s, %s)",
        (email, order_id, token)
    )

    conn.commit()
    cursor.close()
    conn.close()


    return token


# ===============================
# CLEAN EXPIRED SESSIONS
# ===============================
def cleanup_expired_sessions(cursor):
    expiry_time = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    cursor.execute(
        "DELETE FROM active_sessions WHERE last_active < %s",
        (expiry_time.isoformat(),)
    )


# ===============================
# VERIFY TOKEN + MANAGE SESSION
# ===============================
def verify_and_register_session(token, session_id):
    token = token.strip()

    conn = get_db()
    cursor = conn.cursor()


    # ✅ Check token exists
    cursor.execute(
        "SELECT id FROM payments WHERE access_token=%s",
        (token,)
    )
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Invalid token"


    # ✅ Cleanup expired sessions
    cleanup_expired_sessions(cursor)

    # ✅ Check if session already active
    cursor.execute(
        "SELECT id FROM active_sessions WHERE session_id=%s",
        (session_id,)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE active_sessions SET last_active=%s WHERE session_id=%s",
            (datetime.utcnow().isoformat(), session_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return True, "Session refreshed"

    # ✅ Count active sessions
    cursor.execute(
        "SELECT COUNT(*) FROM active_sessions WHERE access_token=%s",
        (token,)
    )
    active_count = cursor.fetchone()[0]

    session_replaced = False

    # ✅ If limit reached → remove oldest session
    if active_count >= MAX_CONCURRENT_USERS:
        cursor.execute("""
            SELECT id FROM active_sessions
            WHERE access_token=%s
            ORDER BY last_active ASC
            LIMIT 1
        """, (token,))

        oldest = cursor.fetchone()

        if oldest:
            cursor.execute(
                "DELETE FROM active_sessions WHERE id=%s",
                (oldest[0],)
            )
            session_replaced = True

    # ✅ Register new session
    cursor.execute(
        "INSERT INTO active_sessions (access_token, session_id, last_active) VALUES (%s, %s, %s)",
        (token, session_id, datetime.utcnow().isoformat())
    )

    conn.commit()
    cursor.close()
    conn.close()

    if session_replaced:
        return True, "Session replaced"

    return True, "Session registered"

def get_all_payments():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT email, access_token, created_at
        FROM payments
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "email": r[0],
            "token": r[1],
            "created_at": str(r[2])
        }
        for r in rows
    ]
