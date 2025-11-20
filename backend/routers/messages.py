import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..database.models import Message, Conversation, User
from ..services.vector_store import vector_store
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/messages", tags=["messages"])


class MessageEdit(BaseModel):
    content: str


class MessageCreate(BaseModel):
    content: str
    mode: str = "auto"
    input_type: str = "text"  # text, voice, voice_live
    journal_only: bool = False
    emotion_data: Optional[dict] = None


@router.put("/{message_id}")
async def edit_message(
    message_id: int,
    edit: MessageEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit a message and re-embed in RAG."""
    # Find message and verify ownership
    msg = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    ).first()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Update message
    old_content = msg.content
    msg.content = edit.content
    msg.updated_at = datetime.utcnow()
    db.commit()

    # Re-embed in vector store
    try:
        await vector_store.delete_entry(f"msg_{message_id}")
        await vector_store.add_entry(
            entry_id=f"msg_{message_id}",
            content=edit.content,
            metadata={
                "user_id": current_user.id,
                "conversation_id": msg.conversation_id,
                "message_id": message_id,
                "role": msg.role,
                "timestamp": msg.created_at.isoformat(),
                "edited": True
            }
        )
        logger.info(f"Re-embedded edited message {message_id}")
    except Exception as e:
        logger.error(f"Failed to re-embed message: {e}")

    return {
        "id": message_id,
        "content": edit.content,
        "updated_at": msg.updated_at.isoformat(),
        "status": "updated"
    }


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a message from DB and RAG."""
    # Find message and verify ownership
    msg = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    ).first()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Delete audio file if exists
    if msg.audio_file_path and os.path.exists(msg.audio_file_path):
        os.remove(msg.audio_file_path)

    # Delete from vector store
    try:
        await vector_store.delete_entry(f"msg_{message_id}")
        logger.info(f"Deleted message {message_id} from vector store")
    except Exception as e:
        logger.error(f"Failed to delete from vector store: {e}")

    # Delete from database
    db.delete(msg)
    db.commit()

    return {"status": "deleted", "id": message_id}


@router.get("/{message_id}/audio")
async def get_message_audio(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audio file for a message."""
    msg = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    ).first()

    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if not msg.audio_file_path or not os.path.exists(msg.audio_file_path):
        raise HTTPException(status_code=404, detail="Audio not found")

    return FileResponse(
        msg.audio_file_path,
        media_type="audio/webm",
        filename=f"message_{message_id}.webm"
    )


@router.post("/{conversation_id}/journal")
async def create_journal_entry(
    conversation_id: int,
    content: str,
    audio: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a journal-only entry (no AI response)."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save audio if provided
    audio_path = None
    if audio:
        audio_dir = f"./data/audio/{current_user.id}"
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = f"{audio_dir}/{datetime.utcnow().timestamp()}.webm"
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

    # Create message
    msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        input_type="voice" if audio else "text",
        audio_file_path=audio_path,
        journal_only=1
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Embed in vector store
    try:
        await vector_store.add_entry(
            entry_id=f"msg_{msg.id}",
            content=content,
            metadata={
                "user_id": current_user.id,
                "conversation_id": conversation_id,
                "message_id": msg.id,
                "role": "user",
                "journal_only": True,
                "timestamp": msg.created_at.isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Failed to embed journal entry: {e}")

    return {
        "id": msg.id,
        "content": content,
        "journal_only": True,
        "has_audio": bool(audio_path),
        "created_at": msg.created_at.isoformat()
    }
