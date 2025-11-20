from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    picture = Column(String(500), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String(255), nullable=True)
    mode = Column(String(50), default="auto")  # auto, architect, simulator, scribe

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(50))  # user, assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # AI metadata
    ai_provider = Column(String(50), nullable=True)  # gemini, deepseek, claude
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    # Emotion data from Hume
    emotion_data = Column(JSON, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")


class EmotionLog(Base):
    __tablename__ = "emotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Top emotions detected
    primary_emotion = Column(String(50))
    emotion_scores = Column(JSON)  # Full emotion breakdown

    # Voice prosody metrics
    pitch = Column(Float, nullable=True)
    speech_rate = Column(Float, nullable=True)


class UsageTracking(Base):
    __tablename__ = "usage_tracking"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow)
    provider = Column(String(50))
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    source = Column(String(50))  # local, google_drive
    google_drive_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_synced = Column(DateTime, nullable=True)
    embedded = Column(Integer, default=0)  # 0: not embedded, 1: embedded
