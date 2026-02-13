from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.db.database import Base


class AccessToken(Base):
    __tablename__ = "access_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("UserSession", back_populates="token")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True)
    token_id = Column(Integer, ForeignKey("access_tokens.id"))
    last_seen = Column(DateTime, default=datetime.utcnow)

    token = relationship("AccessToken", back_populates="sessions")
