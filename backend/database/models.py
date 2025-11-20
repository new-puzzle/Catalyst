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

    # User preferences
    preferences = Column(JSON, default=dict)  # {hume_enabled: true, voice_mode: "hume"|"browser"|"live"}

    conversations = relationship("Conversation", back_populates="user")
    state_summaries = relationship("UserState", back_populates="user")


class UserState(Base):
    """Daily/periodic summary of user's state for AI context."""
    __tablename__ = "user_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    period_type = Column(String(50))  # daily, weekly

    # AI-generated summary
    summary = Column(Text)
    themes = Column(JSON)  # Key themes detected
    emotional_trends = Column(JSON)  # Emotion patterns
    goals_progress = Column(JSON)  # Goal tracking
    recommendations = Column(JSON)

    user = relationship("User", back_populates="state_summaries")


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
    updated_at = Column(DateTime, nullable=True)

    # Input type and audio
    input_type = Column(String(50), default="text")  # text, voice, voice_live
    audio_file_path = Column(String(500), nullable=True)

    # AI metadata
    ai_provider = Column(String(50), nullable=True)  # gemini, deepseek, claude
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)

    # Emotion data from Hume
    emotion_data = Column(JSON, nullable=True)

    # Journal-only flag (no AI response requested)
    journal_only = Column(Integer, default=0)

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
