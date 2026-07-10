from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default=["ai:chat", "ai:embed", "ai:search"])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("ChatSession", back_populates="user",
        cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user",
        cascade="all, delete-orphan")