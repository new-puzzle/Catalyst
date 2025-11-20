import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..database.models import User, Message, Conversation, UserState
from .ai_router import ai_router

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Will be closed after use


async def generate_daily_summary(user_id: int, db: Session):
    """Generate daily summary for a user."""
    yesterday = datetime.utcnow() - timedelta(days=1)

    # Get messages from last 24 hours
    messages = (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Message.created_at >= yesterday
        )
        .order_by(Message.created_at)
        .all()
    )

    if not messages:
        return None

    # Build content for analysis
    content = "\n\n".join([
        f"[{m.created_at.strftime('%H:%M')}] {m.role}: {m.content}"
        for m in messages
    ])

    # Get emotion data
    emotions = [m.emotion_data for m in messages if m.emotion_data]

    prompt = f"""Analyze this user's journal entries from the past 24 hours and create a brief daily summary.

Entries:
{content}

Emotional data (if available): {emotions}

Provide:
1. A 2-3 sentence summary of the day
2. Key themes (as JSON array)
3. Emotional patterns noticed (as JSON object)
4. Any recommendations for tomorrow

Format response as JSON with keys: summary, themes, emotional_trends, recommendations"""

    try:
        response = await ai_router.route(
            messages=[
                {"role": "system", "content": "You are analyzing journal entries. Respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            mode="scribe"  # Use Claude for analysis
        )

        # Parse response (simplified - in production use proper JSON parsing)
        import json
        try:
            data = json.loads(response["content"])
        except:
            data = {
                "summary": response["content"],
                "themes": [],
                "emotional_trends": {},
                "recommendations": []
            }

        # Save to database
        state = UserState(
            user_id=user_id,
            period_type="daily",
            summary=data.get("summary", ""),
            themes=data.get("themes", []),
            emotional_trends=data.get("emotional_trends", {}),
            goals_progress={},
            recommendations=data.get("recommendations", [])
        )
        db.add(state)
        db.commit()

        logger.info(f"Generated daily summary for user {user_id}")
        return state

    except Exception as e:
        logger.error(f"Failed to generate daily summary: {e}")
        return None


async def generate_weekly_synthesis(user_id: int, db: Session):
    """Generate weekly synthesis for a user."""
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Get all messages from the week
    messages = (
        db.query(Message)
        .join(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Message.created_at >= week_ago
        )
        .order_by(Message.created_at)
        .all()
    )

    # Get daily summaries
    daily_summaries = (
        db.query(UserState)
        .filter(
            UserState.user_id == user_id,
            UserState.period_type == "daily",
            UserState.created_at >= week_ago
        )
        .all()
    )

    if not messages:
        return None

    content = "\n\n".join([
        f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {m.role}: {m.content[:200]}"
        for m in messages[:100]  # Limit for context
    ])

    daily_content = "\n".join([
        f"Day {i+1}: {s.summary}" for i, s in enumerate(daily_summaries)
    ])

    prompt = f"""Create a comprehensive weekly synthesis of this user's journal.

Daily Summaries:
{daily_content if daily_content else 'No daily summaries available'}

Sample Entries:
{content}

Provide a thoughtful weekly review with:
1. Overall summary of the week
2. Key themes and patterns
3. Emotional journey
4. Progress on any goals mentioned
5. Actionable recommendations for next week

Format as JSON with keys: summary, themes, emotional_trends, goals_progress, recommendations"""

    try:
        response = await ai_router.route(
            messages=[
                {"role": "system", "content": "You are a thoughtful life coach analyzing weekly journal data."},
                {"role": "user", "content": prompt}
            ],
            mode="scribe"
        )

        import json
        try:
            data = json.loads(response["content"])
        except:
            data = {
                "summary": response["content"],
                "themes": [],
                "emotional_trends": {},
                "goals_progress": {},
                "recommendations": []
            }

        state = UserState(
            user_id=user_id,
            period_type="weekly",
            summary=data.get("summary", ""),
            themes=data.get("themes", []),
            emotional_trends=data.get("emotional_trends", {}),
            goals_progress=data.get("goals_progress", {}),
            recommendations=data.get("recommendations", [])
        )
        db.add(state)
        db.commit()

        logger.info(f"Generated weekly synthesis for user {user_id}")
        return state

    except Exception as e:
        logger.error(f"Failed to generate weekly synthesis: {e}")
        return None


async def run_daily_summaries():
    """Run daily summaries for all users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            await generate_daily_summary(user.id, db)
    finally:
        db.close()


async def run_weekly_syntheses():
    """Run weekly synthesis for all users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            await generate_weekly_synthesis(user.id, db)
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    # Daily summary at 11 PM every day
    scheduler.add_job(
        run_daily_summaries,
        CronTrigger(hour=23, minute=0),
        id="daily_summaries",
        replace_existing=True
    )

    # Weekly synthesis on Sunday at 10 PM
    scheduler.add_job(
        run_weekly_syntheses,
        CronTrigger(day_of_week="sun", hour=22, minute=0),
        id="weekly_syntheses",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started with daily and weekly jobs")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
