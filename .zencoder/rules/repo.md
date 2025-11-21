---
description: Repository Information Overview
alwaysApply: true
---

# Catalyst - Repository Information

## Repository Summary
Catalyst is a full-stack AI-powered journaling companion application with voice-first experience. It provides four conversation modes (Auto, Architect, Simulator, Scribe), real-time AI responses, emotion detection, smart memory using RAG (Retrieval-Augmented Generation), and automatic insights through daily/weekly summaries. The application integrates multiple AI models (Gemini Flash, DeepSeek, Claude) and includes Google Sign-In authentication with privacy-focused local database storage.

## Repository Structure
The repository is organized as a multi-project application with frontend and backend components:
- **backend/**: Python FastAPI server with AI orchestration, vector store, and database management
- **frontend/**: React TypeScript application with Vite build system and Tailwind CSS styling
- **data/**: Application data storage directory for databases and vector stores
- **.zencoder/**: Zencoder-related documentation and rules

### Main Repository Components
- **Backend API Server**: FastAPI application handling conversations, authentication, voice processing, and AI integration
- **Frontend UI**: React-based responsive web interface with real-time conversation support
- **Vector Store**: ChromaDB integration for semantic search and RAG functionality
- **Authentication**: Google OAuth integration with JWT token management
- **Scheduler**: Background tasks for automatic daily/weekly summaries and scheduled insights

## Projects

### Backend (Python/FastAPI)
**Configuration File**: ackend/config.py

#### Language & Runtime
**Language**: Python
**Runtime Version**: Python 3.8+
**Build System**: pip package manager
**Package Manager**: pip

#### Dependencies
**Main Dependencies**:
- fastapi==0.121.3 - Web framework
- uvicorn[standard]==0.27.0 - ASGI server
- sqlalchemy==2.0.25 - ORM for database
- pydantic==2.12.4 & pydantic-settings==2.12.0 - Data validation
- chromadb==0.4.22 - Vector database for RAG
- python-jose[cryptography]==3.3.0 - JWT authentication
- httpx==0.26.0 - HTTP client
- websockets==12.0 - WebSocket support
- apscheduler==3.10.4 - Background task scheduling
- python-multipart==0.0.6 - File upload handling

#### Build & Installation
`ash
cd backend
pip install -r requirements.txt
`

#### Main Entry Point
- **Application**: ackend/main.py - FastAPI application initialization
- **Configuration**: ackend/config.py - Environment-based settings management
- **Database**: SQLite at ./data/db/conversations.db with vector store at ./data/db/vector_store

#### Routers & Services
**API Routers**:
- outers/auth.py - Google OAuth and JWT authentication
- outers/conversations.py - Conversation management endpoints
- outers/messages.py - Message CRUD operations
- outers/voice.py - Voice input/output processing
- outers/synthesis.py - Audio synthesis endpoints
- outers/documents.py - Document management

**Core Services**:
- services/ai_router.py - AI model routing and orchestration
- services/vector_store.py - RAG and semantic search implementation
- services/scheduler.py - Background job scheduling for insights
- database/ - Database initialization and models

#### Configuration
**Environment Variables** (from config.py):
- API Keys: gemini_api_key, deepseek_api_key, nthropic_api_key
- OAuth: google_client_id, google_client_secret, google_redirect_uri
- Database: database_url, chroma_persist_dir
- CORS: cors_origins (default: localhost:5173, localhost:3000)
- JWT: jwt_secret_key, jwt_expiration_minutes (7 days default)

#### Run Command
`ash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
`

### Frontend (TypeScript/React)
**Configuration File**: rontend/package.json

#### Language & Runtime
**Language**: TypeScript 5.2.2
**Runtime**: Node.js (via Vite development server)
**Build System**: Vite 5.0.8
**Package Manager**: npm

#### Dependencies
**Main Dependencies**:
- react==18.2.0 & react-dom==18.2.0 - UI framework
- framer-motion==10.18.0 - Animation library
- lucide-react==0.303.0 - Icon library

**Development Dependencies**:
- TypeScript configuration (@types/react, @types/react-dom)
- Vite with React plugin (@vitejs/plugin-react)
- ESLint with TypeScript support
- PostCSS & Tailwind CSS for styling
- Testing framework support

#### Build & Installation
`ash
cd frontend
npm install
`

#### Build Commands
`ash
npm run dev      # Development server (port 3000, proxies to http://localhost:8080)
npm run build    # TypeScript compilation and Vite build
npm run lint     # ESLint code quality check
npm run preview  # Preview production build
`

#### Project Structure
- src/components/ - React UI components
- src/hooks/ - Custom React hooks
- src/services/ - API service layer
- src/types/ - TypeScript type definitions
- src/main.tsx - Application entry point
- src/App.tsx - Root component

#### Configuration Files
- ite.config.ts - Vite build configuration with React plugin and API proxy
- 	sconfig.json - TypeScript compiler options
- 	ailwind.config.js - Tailwind CSS customization
- postcss.config.js - PostCSS processing

#### Development Server
- **Port**: 3000
- **API Proxy**: /api routes forwarded to http://localhost:8080

## Technology Stack Summary
- **Backend**: FastAPI (Python), SQLAlchemy ORM, ChromaDB vector store
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Authentication**: Google OAuth 2.0, JWT tokens
- **AI Models**: Gemini Flash, DeepSeek, Claude (via API integration)
- **Database**: SQLite
- **Real-time**: WebSockets
- **Task Scheduling**: APScheduler for automated insights

## Cost Optimization
The application implements multi-model AI strategy with cost tracking per 1M tokens:
- Gemini Flash: .075/1M tokens (daily journaling)
- DeepSeek: .14/1M tokens (planning tasks)
- Claude: .00/1M tokens (premium writing tasks)
