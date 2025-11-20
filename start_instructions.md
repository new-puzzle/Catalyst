# Catalyst - Start Instructions

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

## Quick Start

### 1. Clone and Setup

```bash
cd Catalyst
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example .env
```

### 3. Configure Environment Variables

Edit `backend/.env`:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=generate_a_random_string_here
GOOGLE_CLIENT_ID=your_google_client_id
CORS_ORIGINS=http://localhost:3000

# Optional (for additional features)
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUME_API_KEY=your_hume_api_key
```

### 4. Start Backend

```bash
# From backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Backend will be available at `http://localhost:8080`

### 5. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_HUME_API_KEY=your_hume_api_key  # Optional
```

### 6. Start Frontend

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Getting API Keys

### Google Cloud (Required)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Google+ API" or "People API"
4. Create OAuth 2.0 credentials
5. Add `http://localhost:3000` to authorized origins
6. Copy the Client ID

### Gemini API (Required)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Get an API key
3. Enable the Generative Language API in Google Cloud

### DeepSeek (Optional)
1. Go to [DeepSeek](https://platform.deepseek.com/)
2. Create account and get API key

### Anthropic (Optional)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create account and get API key

### Hume AI (Optional)
1. Go to [Hume AI](https://hume.ai/)
2. Create account and get API key

## Verify Installation

1. Open `http://localhost:3000` in browser
2. Click "Sign in with Google"
3. Start a conversation
4. Check backend logs for any errors

## Common Issues

### CORS Errors
- Ensure `CORS_ORIGINS` in backend `.env` matches your frontend URL
- Include the full URL with port: `http://localhost:3000`

### Database Errors
- Delete `backend/catalyst.db` to reset database
- Delete `backend/data/chroma` to reset vector store

### API Key Issues
- Verify API keys are correct
- Check Google Cloud API is enabled
- Ensure billing is set up for paid APIs

### Port Conflicts
Change ports in:
- `frontend/vite.config.ts` (line 7)
- Backend start command: `--port XXXX`
- Update `CORS_ORIGINS` accordingly

## Production Deployment

### Backend
```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
```

### Frontend
```bash
# Build for production
npm run build

# Serve with any static file server
npx serve -s dist -l 3000
```

## Directory Structure After Setup

```
Catalyst/
├── backend/
│   ├── .env                 # Your environment variables
│   ├── catalyst.db          # SQLite database (created on first run)
│   └── data/
│       ├── chroma/          # Vector database
│       └── audio/           # Voice recordings
├── frontend/
│   ├── .env                 # Frontend environment
│   └── node_modules/        # Dependencies
└── venv/                    # Python virtual environment
```

## Useful Commands

```bash
# Backend logs
tail -f backend/logs/app.log

# Reset database
rm backend/catalyst.db

# Clear vector store
rm -rf backend/data/chroma

# Update dependencies
pip install -r requirements.txt --upgrade
npm update

# Check running ports
lsof -i :3000
lsof -i :8080
```
