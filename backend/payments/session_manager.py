from backend.db.database import SessionLocal
from backend.payments.models import AccessToken, UserSession
from datetime import datetime, timedelta
import os

MAX_SESSIONS = int(os.getenv("MAX_ACTIVE_SESSIONS", 3))
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_MIN", 60))


def verify_and_register_session(token_value, session_id):
    db = SessionLocal()

    token = db.query(AccessToken).filter(
        AccessToken.token == token_value
    ).first()

    if not token:
        return False, "Invalid token"

    now = datetime.utcnow()
    timeout = timedelta(minutes=SESSION_TIMEOUT)

    # Remove expired sessions
    active_sessions = []
    for s in token.sessions:
        if now - s.last_seen < timeout:
            active_sessions.append(s)
        else:
            db.delete(s)
    
    db.commit()



    # Check existing session
    existing = next((s for s in active_sessions if s.session_id == session_id), None)

    if existing:
        existing.last_seen = now
        db.commit()
        return True, "Session refreshed"

    if len(active_sessions) >= MAX_SESSIONS:
        return False, "Max users reached"

    new_session = UserSession(
        session_id=session_id,
        token_id=token.id,
        last_seen=now
    )

    db.add(new_session)
    db.commit()
    db.close()

    return True, "Session registered"
