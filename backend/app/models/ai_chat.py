from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, JSON
from app.config.database import Base
from datetime import datetime, timezone
import enum


class ChatMessageStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class AIChatSession(Base):
    __tablename__ = "ai_chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False, default="New chat")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_session_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    extra = Column(JSON, nullable=True)
    status = Column(
        SAEnum(ChatMessageStatus),
        nullable=False,
        default=ChatMessageStatus.COMPLETED
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
