from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..database.models import Conversation, Message, UsageTracking, User
from ..models.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationSummary,
    MessageCreate,
    MessageResponse,
    UsageStats,
)
from ..services.ai_router import ai_router
from .auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse)
def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_conv = Conversation(title=conv.title, mode=conv.mode, user_id=current_user.id)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv


@router.get("/", response_model=List[ConversationSummary])
def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for conv in conversations:
        result.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                mode=conv.mode,
                created_at=conv.created_at,
                message_count=len(conv.messages),
            )
        )
    return result


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "deleted"}


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=message.content,
        emotion_data=message.emotion_data,
    )
    db.add(user_msg)
    db.commit()

    # Build message history for context
    history = [{"role": "system", "content": get_system_prompt(message.mode)}]
    for msg in conv.messages:
        history.append({"role": msg.role, "content": msg.content})
    history.append({"role": "user", "content": message.content})

    # Route to AI
    ai_response = await ai_router.route(
        messages=history,
        mode=message.mode,
        override_provider=message.override_provider,
    )

    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response["content"],
        ai_provider=ai_response["provider"],
        tokens_used=ai_response["tokens_used"],
        cost=ai_response["cost"],
    )
    db.add(assistant_msg)

    # Track usage
    usage = UsageTracking(
        provider=ai_response["provider"],
        tokens_input=ai_response["tokens_used"] // 2,
        tokens_output=ai_response["tokens_used"] // 2,
        total_cost=ai_response["cost"],
    )
    db.add(usage)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


def get_system_prompt(mode: str) -> str:
    prompts = {
        "auto": """You are Catalyst, an empathetic AI journaling companion. Help users reflect on their thoughts and feelings. Be warm, supportive, and help them gain insights from their daily experiences. Keep responses conversational and encouraging.""",
        "architect": """You are Catalyst in Architect mode. Help users structure their goals, create action plans, and break down complex ideas into manageable steps. Be organized, analytical, and provide clear frameworks. Use bullet points and numbered lists when helpful.""",
        "simulator": """You are Catalyst in Simulator mode. Help users practice conversations, prepare for interviews, or work through hypothetical scenarios. Provide realistic responses and constructive feedback. Adapt your tone to match the simulation context.""",
        "scribe": """You are Catalyst in Scribe mode. Transform user's rough thoughts into polished, professional content. Whether it's emails, social posts, or documents, craft clear, well-structured text that maintains the user's voice while elevating the quality.""",
    }
    return prompts.get(mode, prompts["auto"])


@router.get("/stats/usage", response_model=UsageStats)
def get_usage_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(days=days)

    usage = db.query(UsageTracking).filter(UsageTracking.date >= since).all()

    total_cost = sum(u.total_cost for u in usage)
    by_provider = {}
    for u in usage:
        if u.provider not in by_provider:
            by_provider[u.provider] = 0
        by_provider[u.provider] += u.total_cost

    message_count = db.query(Message).filter(Message.created_at >= since).count()

    return UsageStats(
        period=f"Last {days} days",
        total_cost=round(total_cost, 4),
        by_provider={k: round(v, 4) for k, v in by_provider.items()},
        total_messages=message_count,
    )
