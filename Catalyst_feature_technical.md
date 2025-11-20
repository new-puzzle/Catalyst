# Catalyst - Technical Specifications

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI   │────▶│  AI APIs    │
│  Frontend   │◀────│   Backend   │◀────│  (Multi)    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌──────────┐
              │ SQLite  │   │ ChromaDB │
              │   DB    │   │  Vector  │
              └─────────┘   └──────────┘
```

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** build tool
- **TailwindCSS** for styling
- **Framer Motion** for animations
- **Lucide React** for icons

### Backend
- **FastAPI** (Python 3.10+)
- **SQLAlchemy** ORM
- **Pydantic** for validation
- **APScheduler** for background tasks

### Databases
- **SQLite** - User data, conversations, messages
- **ChromaDB** - Vector embeddings for RAG

### AI Providers
| Provider | Model | Use Case | Cost/1M tokens |
|----------|-------|----------|----------------|
| Google | Gemini 1.5 Flash | Daily journaling, embeddings | $0.075 |
| DeepSeek | deepseek-chat | Planning, architecture | $0.14 |
| Anthropic | Claude Sonnet 4 | Quality writing, simulation | $3.00 |

### Voice
- **Gemini Live API** - Real-time bidirectional voice streaming
- **Hume AI** (optional) - Emotion detection from voice

## API Endpoints

### Authentication
```
POST /auth/google        - Google OAuth login
GET  /auth/me            - Get current user
GET  /auth/preferences   - Get user preferences
PUT  /auth/preferences   - Update preferences
```

### Conversations
```
POST /conversations/                    - Create conversation
GET  /conversations/                    - List conversations
GET  /conversations/{id}                - Get conversation
DELETE /conversations/{id}              - Delete conversation
POST /conversations/{id}/messages       - Send message
GET  /conversations/stats/usage         - Usage statistics
```

### Messages
```
PUT    /messages/{id}        - Edit message
DELETE /messages/{id}        - Delete message
GET    /messages/{id}/audio  - Get audio file
POST   /messages/{conv}/journal - Create journal-only entry
```

### Voice
```
WS  /voice/stream   - Real-time voice WebSocket
GET /voice/voices   - List available voices
```

### Documents
```
POST /documents/upload   - Upload file
GET  /documents/export   - Export conversations
```

### Synthesis
```
GET /synthesis/weekly    - Get weekly synthesis
```

## Database Schema

### Users
```sql
- id, email, name, picture, google_id
- preferences (JSON): {hume_enabled, voice_mode}
- created_at
```

### Conversations
```sql
- id, user_id, title, mode, created_at
```

### Messages
```sql
- id, conversation_id, role, content
- input_type (text/voice/voice_live)
- audio_file_path, emotion_data
- ai_provider, tokens_used, cost
- journal_only, created_at, updated_at
```

### UserState (Summaries)
```sql
- id, user_id, period_type (daily/weekly)
- summary, themes, emotional_trends
- goals_progress, recommendations
```

## RAG System

### Embedding Pipeline
1. User sends message
2. Generate embedding via Gemini `text-embedding-004`
3. Store in ChromaDB with metadata
4. On new message, query similar entries
5. Inject relevant context into system prompt

### Vector Search
- **Distance metric**: Cosine similarity
- **Relevance threshold**: < 0.7
- **Results limit**: 3 entries

## Background Scheduler

### Daily Summary (11 PM)
- Aggregates last 24h messages
- Generates themes, emotional trends
- Stores in UserState table

### Weekly Synthesis (Sunday 10 PM)
- Reviews all week's entries
- Comprehensive analysis
- Goal progress tracking
- Recommendations

## WebSocket Protocol (Voice)

### Client → Server
```json
{"type": "init", "user_id": 1, "conversation_id": 1}
{"type": "audio", "data": "<base64 PCM>"}
{"type": "text", "data": "message"}
{"type": "interrupt"}
{"type": "end_turn"}
```

### Server → Client
```json
{"type": "audio", "data": "<base64>", "mimeType": "..."}
{"type": "text", "data": "transcript"}
{"type": "status", "data": "Connected"}
{"type": "turn_complete", "data": true}
{"type": "error", "data": "message"}
```

## Security

- **JWT tokens** for API authentication
- **Google OAuth 2.0** for user identity
- **CORS** configured per environment
- **Input validation** via Pydantic

## Error Handling

- **502 Bad Gateway** - AI service errors
- **503 Service Unavailable** - Network issues
- **504 Gateway Timeout** - Request timeouts
- All errors logged with context

## Performance

- **Async/await** throughout backend
- **Connection pooling** for databases
- **Singleton** pattern for vector store
- **Optimistic UI** updates on frontend

## File Structure

```
Catalyst/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── __init__.py      # DB setup
│   ├── routers/
│   │   ├── auth.py          # Authentication
│   │   ├── conversations.py # Main chat logic
│   │   ├── messages.py      # CRUD operations
│   │   ├── voice.py         # WebSocket streaming
│   │   ├── documents.py     # File handling
│   │   └── synthesis.py     # AI summaries
│   └── services/
│       ├── ai_router.py     # Multi-AI routing
│       ├── vector_store.py  # ChromaDB RAG
│       └── scheduler.py     # Background jobs
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   ├── components/      # UI components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/api.ts  # API client
│   │   └── types/           # TypeScript types
│   └── vite.config.ts       # Build config
└── data/
    ├── chroma/              # Vector DB
    └── audio/               # Voice recordings
```
