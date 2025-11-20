import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import io
import json

from ..database import get_db
from ..database.models import Document, Conversation, Message, User
from ..services.vector_store import vector_store
from ..config import get_settings
from .auth import get_current_user

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and embed a document for RAG."""
    # Validate file type
    allowed_types = [".txt", ".md", ".json"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    # Save file to disk
    file_dir = f"./data/files/{current_user.id}"
    os.makedirs(file_dir, exist_ok=True)
    file_path = f"{file_dir}/{file.filename}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    # Save to database
    doc = Document(
        filename=file.filename,
        file_path=file_path,
        source="local",
        embedded=0
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Embed in vector store
    try:
        # Split into chunks if long
        chunks = split_text(text_content, max_length=1000)
        for i, chunk in enumerate(chunks):
            await vector_store.add_entry(
                entry_id=f"doc_{doc.id}_chunk_{i}",
                content=chunk,
                metadata={
                    "user_id": current_user.id,
                    "document_id": doc.id,
                    "filename": file.filename,
                    "chunk_index": i,
                    "source": "upload",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        doc.embedded = 1
        db.commit()
        logger.info(f"Embedded document {doc.id} with {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Failed to embed document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to embed document: {str(e)}")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "chunks_embedded": len(chunks),
        "status": "success"
    }


@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all uploaded documents."""
    docs = db.query(Document).filter(
        Document.file_path.like(f"./data/files/{current_user.id}%")
    ).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "embedded": bool(doc.embedded),
            "created_at": doc.created_at.isoformat()
        }
        for doc in docs
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its embeddings."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.file_path.like(f"./data/files/{current_user.id}%")
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store (all chunks)
    for i in range(100):  # Assume max 100 chunks
        try:
            await vector_store.delete_entry(f"doc_{doc.id}_chunk_{i}")
        except:
            break

    # Delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()

    return {"status": "deleted"}


# Export endpoints
@router.get("/export/conversations")
def export_conversations(
    format: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all conversations."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )

    if format == "json":
        data = []
        for conv in conversations:
            data.append({
                "id": conv.id,
                "title": conv.title,
                "mode": conv.mode,
                "created_at": conv.created_at.isoformat(),
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "ai_provider": msg.ai_provider,
                        "emotion_data": msg.emotion_data
                    }
                    for msg in conv.messages
                ]
            })

        return StreamingResponse(
            io.BytesIO(json.dumps(data, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=catalyst_export.json"}
        )

    elif format == "markdown":
        md_content = "# Catalyst Journal Export\n\n"
        for conv in conversations:
            md_content += f"## {conv.title or 'Untitled'} ({conv.mode})\n"
            md_content += f"*{conv.created_at.strftime('%Y-%m-%d %H:%M')}*\n\n"
            for msg in conv.messages:
                role = "You" if msg.role == "user" else "Catalyst"
                md_content += f"**{role}**: {msg.content}\n\n"
            md_content += "---\n\n"

        return StreamingResponse(
            io.BytesIO(md_content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=catalyst_export.md"}
        )

    else:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'markdown'")


@router.get("/export/conversation/{conversation_id}")
def export_single_conversation(
    conversation_id: int,
    format: str = "markdown",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a single conversation."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if format == "markdown":
        md_content = f"# {conv.title or 'Journal Entry'}\n"
        md_content += f"*Mode: {conv.mode} | {conv.created_at.strftime('%Y-%m-%d %H:%M')}*\n\n"

        for msg in conv.messages:
            role = "You" if msg.role == "user" else "Catalyst"
            md_content += f"**{role}**: {msg.content}\n\n"

        return StreamingResponse(
            io.BytesIO(md_content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id}.md"}
        )
    else:
        data = {
            "id": conv.id,
            "title": conv.title,
            "mode": conv.mode,
            "created_at": conv.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in conv.messages
            ]
        }
        return StreamingResponse(
            io.BytesIO(json.dumps(data, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=conversation_{conversation_id}.json"}
        )


def split_text(text: str, max_length: int = 1000) -> List[str]:
    """Split text into chunks for embedding."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text[:max_length]]
