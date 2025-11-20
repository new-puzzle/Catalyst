import logging
import json
import asyncio
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import websockets

from ..config import get_settings
from ..database import SessionLocal
from ..database.models import Conversation, Message
from ..services.vector_store import vector_store

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


async def save_voice_session_to_rag(user_id: int, conversation_id: int, transcripts: list):
    """Save voice session transcripts to database and RAG."""
    if not transcripts:
        return

    db = SessionLocal()
    try:
        for transcript in transcripts:
            msg = Message(
                conversation_id=conversation_id,
                role=transcript["role"],
                content=transcript["content"],
                input_type="voice_live",
                ai_provider="gemini-live" if transcript["role"] == "assistant" else None
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Embed in vector store
            try:
                await vector_store.add_entry(
                    entry_id=f"msg_{msg.id}",
                    content=transcript["content"],
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "message_id": msg.id,
                        "role": transcript["role"],
                        "input_type": "voice_live",
                        "timestamp": msg.created_at.isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to embed voice transcript: {e}")
    finally:
        db.close()

# Gemini Live API configuration
GEMINI_LIVE_MODEL = "gemini-2.0-flash-live-preview"
GEMINI_LIVE_WS_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    Real-time voice conversation using Gemini Live API.

    Protocol:
    - Client sends: {"type": "init", "user_id": int, "conversation_id": int}
    - Client sends: {"type": "audio", "data": "<base64 PCM audio>"}
    - Client sends: {"type": "text", "data": "user message"}
    - Client sends: {"type": "interrupt"} - to interrupt AI response
    - Server sends: {"type": "audio", "data": "<base64 PCM audio>"}
    - Server sends: {"type": "text", "data": "transcript"}
    - Server sends: {"type": "status", "data": "..."}
    """
    await websocket.accept()
    logger.info("Voice stream connected")

    if not settings.gemini_api_key:
        await websocket.send_json({"type": "error", "data": "Gemini API key not configured"})
        await websocket.close()
        return

    gemini_ws = None
    transcripts = []
    user_id = None
    conversation_id = None

    try:
        # Wait for init message with user/conversation IDs
        init_data = await websocket.receive_text()
        init_msg = json.loads(init_data)
        if init_msg.get("type") == "init":
            user_id = init_msg.get("user_id")
            conversation_id = init_msg.get("conversation_id")

        # Connect to Gemini Live API
        gemini_url = f"{GEMINI_LIVE_WS_URL}?key={settings.gemini_api_key}"
        gemini_ws = await websockets.connect(gemini_url)
        logger.info("Connected to Gemini Live API")

        # Send initial setup message
        setup_message = {
            "setup": {
                "model": f"models/{GEMINI_LIVE_MODEL}",
                "generationConfig": {
                    "responseModalities": ["AUDIO", "TEXT"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Aoede"  # Warm, conversational voice
                            }
                        }
                    }
                },
                "systemInstruction": {
                    "parts": [{
                        "text": """You are Catalyst, an empathetic AI journaling companion.
                        Help users reflect on their thoughts and feelings.
                        Be warm, supportive, and conversational.
                        Keep responses concise since this is voice conversation.
                        When the user pauses, encourage them to continue or ask thoughtful questions."""
                    }]
                }
            }
        }
        await gemini_ws.send(json.dumps(setup_message))

        # Wait for setup confirmation
        setup_response = await gemini_ws.recv()
        setup_data = json.loads(setup_response)
        if "setupComplete" in setup_data:
            await websocket.send_json({"type": "status", "data": "Connected to voice AI"})
        else:
            logger.warning(f"Unexpected setup response: {setup_data}")

        # Create tasks for bidirectional streaming
        client_to_gemini = asyncio.create_task(
            forward_client_to_gemini(websocket, gemini_ws, transcripts)
        )
        gemini_to_client = asyncio.create_task(
            forward_gemini_to_client(websocket, gemini_ws, transcripts)
        )

        # Wait for either task to complete (client disconnect or error)
        done, pending = await asyncio.wait(
            [client_to_gemini, gemini_to_client],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()

    except websockets.exceptions.WebSocketException as e:
        logger.error(f"Gemini WebSocket error: {e}")
        await websocket.send_json({"type": "error", "data": f"Gemini connection error: {str(e)}"})
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Voice stream error: {e}")
        await websocket.send_json({"type": "error", "data": str(e)})
    finally:
        if gemini_ws:
            await gemini_ws.close()

        # Save transcripts to RAG
        if user_id and conversation_id and transcripts:
            try:
                await save_voice_session_to_rag(user_id, conversation_id, transcripts)
                logger.info(f"Saved {len(transcripts)} transcripts to RAG")
            except Exception as e:
                logger.error(f"Failed to save voice session: {e}")

        logger.info("Voice stream closed")


async def forward_client_to_gemini(client_ws: WebSocket, gemini_ws, transcripts: list):
    """Forward messages from client to Gemini Live API."""
    try:
        while True:
            data = await client_ws.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "audio":
                # Forward audio to Gemini
                audio_data = message.get("data")
                gemini_message = {
                    "realtimeInput": {
                        "mediaChunks": [{
                            "mimeType": "audio/pcm;rate=16000",
                            "data": audio_data
                        }]
                    }
                }
                await gemini_ws.send(json.dumps(gemini_message))

            elif msg_type == "text":
                # Send text input
                text_content = message.get("data")
                # Collect user transcript
                transcripts.append({"role": "user", "content": text_content})
                gemini_message = {
                    "clientContent": {
                        "turns": [{
                            "role": "user",
                            "parts": [{"text": text_content}]
                        }],
                        "turnComplete": True
                    }
                }
                await gemini_ws.send(json.dumps(gemini_message))

            elif msg_type == "interrupt":
                # Interrupt current response (barge-in)
                # Send empty audio to signal interruption
                await gemini_ws.send(json.dumps({
                    "realtimeInput": {
                        "mediaChunks": []
                    }
                }))

            elif msg_type == "end_turn":
                # Signal end of user turn
                await gemini_ws.send(json.dumps({
                    "clientContent": {
                        "turnComplete": True
                    }
                }))

            elif msg_type == "user_transcript":
                # Client sent transcription of voice input
                text_content = message.get("data")
                if text_content:
                    transcripts.append({"role": "user", "content": text_content})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Client to Gemini error: {e}")


async def forward_gemini_to_client(client_ws: WebSocket, gemini_ws, transcripts: list):
    """Forward responses from Gemini Live API to client."""
    current_response = []
    try:
        async for message in gemini_ws:
            data = json.loads(message)

            # Handle different response types
            if "serverContent" in data:
                content = data["serverContent"]

                # Model turn content
                if "modelTurn" in content:
                    model_turn = content["modelTurn"]
                    for part in model_turn.get("parts", []):
                        # Text response
                        if "text" in part:
                            current_response.append(part["text"])
                            await client_ws.send_json({
                                "type": "text",
                                "data": part["text"]
                            })

                        # Audio response
                        if "inlineData" in part:
                            inline_data = part["inlineData"]
                            if "audio" in inline_data.get("mimeType", ""):
                                await client_ws.send_json({
                                    "type": "audio",
                                    "data": inline_data["data"],
                                    "mimeType": inline_data["mimeType"]
                                })

                # Turn complete signal
                if content.get("turnComplete"):
                    # Save assistant response to transcripts
                    if current_response:
                        full_response = "".join(current_response)
                        transcripts.append({"role": "assistant", "content": full_response})
                        current_response = []

                    await client_ws.send_json({
                        "type": "turn_complete",
                        "data": True
                    })

                # Interrupted signal
                if content.get("interrupted"):
                    # Save partial response
                    if current_response:
                        full_response = "".join(current_response)
                        transcripts.append({"role": "assistant", "content": full_response})
                        current_response = []

                    await client_ws.send_json({
                        "type": "interrupted",
                        "data": True
                    })

            # Handle tool calls if any
            elif "toolCall" in data:
                await client_ws.send_json({
                    "type": "tool_call",
                    "data": data["toolCall"]
                })

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Gemini to client error: {e}")


@router.get("/voices")
async def list_voices():
    """List available voices for Gemini Live."""
    return {
        "voices": [
            {"name": "Aoede", "description": "Warm, conversational"},
            {"name": "Charon", "description": "Deep, authoritative"},
            {"name": "Fenrir", "description": "Energetic, youthful"},
            {"name": "Kore", "description": "Calm, soothing"},
            {"name": "Puck", "description": "Friendly, playful"}
        ],
        "default": "Aoede"
    }
