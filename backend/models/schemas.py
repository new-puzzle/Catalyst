from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageCreate(BaseModel):
    content: str
    mode: str = "auto"  # auto, architect, simulator, scribe
    override_provider: Optional[str] = None
    emotion_data: Optional[dict] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    ai_provider: Optional[str]
    tokens_used: Optional[int]
    cost: Optional[float]
    emotion_data: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    mode: str = "auto"


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    mode: str
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: int
    title: Optional[str]
    mode: str
    created_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class AIRouterRequest(BaseModel):
    messages: List[dict]
    mode: str = "auto"
    override_provider: Optional[str] = None


class AIRouterResponse(BaseModel):
    content: str
    provider: str
    tokens_used: int
    cost: float


class WeeklySynthesisResponse(BaseModel):
    summary: str
    themes: List[str]
    emotional_patterns: List[dict]
    goal_progress: List[dict]
    recommendations: List[str]
    generated_at: datetime


class UsageStats(BaseModel):
    period: str
    total_cost: float
    by_provider: dict
    total_messages: int


class EmotionAnalysis(BaseModel):
    primary_emotion: str
    confidence: float
    all_emotions: dict
