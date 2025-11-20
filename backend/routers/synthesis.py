from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db
from ..database.models import Message, EmotionLog
from ..models.schemas import WeeklySynthesisResponse
from ..services.ai_router import ai_router

router = APIRouter(prefix="/synthesis", tags=["synthesis"])


@router.get("/weekly", response_model=WeeklySynthesisResponse)
async def weekly_synthesis(db: Session = Depends(get_db)):
    """Generate weekly synthesis using Claude for deep analysis."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Get all messages from the past week
    messages = (
        db.query(Message)
        .filter(Message.created_at >= week_ago)
        .order_by(Message.created_at)
        .all()
    )

    # Get emotion logs
    emotion_logs = (
        db.query(EmotionLog)
        .filter(EmotionLog.timestamp >= week_ago)
        .all()
    )

    # Build context for synthesis
    journal_content = "\n\n".join(
        [f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.role}: {m.content}"
         for m in messages]
    )

    emotion_summary = ""
    if emotion_logs:
        emotions = {}
        for log in emotion_logs:
            if log.primary_emotion not in emotions:
                emotions[log.primary_emotion] = 0
            emotions[log.primary_emotion] += 1
        emotion_summary = f"Emotion frequency: {emotions}"

    synthesis_prompt = f"""Analyze this week's journal entries and provide a synthesis.

Journal Entries:
{journal_content if journal_content else "No entries this week."}

Emotional Data:
{emotion_summary if emotion_summary else "No emotion data available."}

Please provide:
1. A brief summary of the week
2. Key themes that emerged
3. Emotional patterns observed
4. Progress on any mentioned goals
5. Recommendations for the coming week

Format your response as a thoughtful, supportive synthesis that helps the user gain insight into their week."""

    # Use Claude for synthesis (high-quality analysis)
    response = await ai_router.route(
        messages=[
            {"role": "system", "content": "You are an insightful life coach analyzing journal entries."},
            {"role": "user", "content": synthesis_prompt},
        ],
        mode="scribe",  # Uses Claude
    )

    # Parse response into structured format
    # In production, use structured output from the AI
    return WeeklySynthesisResponse(
        summary=response["content"],
        themes=["Reflection", "Growth", "Planning"],  # Placeholder
        emotional_patterns=[
            {"emotion": "contemplative", "frequency": "high"},
        ],
        goal_progress=[
            {"goal": "Weekly journaling", "status": "in_progress"},
        ],
        recommendations=[
            "Continue daily reflection practice",
            "Set specific times for journaling",
        ],
        generated_at=datetime.utcnow(),
    )
