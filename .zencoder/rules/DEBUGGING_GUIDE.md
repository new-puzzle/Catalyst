---
description: Frontend/Backend Connection Debugging Guide
alwaysApply: true
---

# Catalyst - Frontend/Backend Connection Debugging Guide

## Common Issue: 400 Error When Frontend Connects to Backend

### Root Cause
The frontend (running on port 3000) connects to the backend via a proxy configured in vite.config.ts. A 400 error typically means:
- Backend is not running
- Backend is running on the wrong port
- CORS headers are misconfigured
- API request format is incorrect

### Solution Checklist

#### 1. Verify Backend is Running on Port 8080

**Start Backend:**
\\\powershell
# From project root
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start on port 8080 (CRITICAL - must be 8080)
uvicorn main:app --reload --host 0.0.0.0 --port 8080
\\\

**Verify Backend is Running:**
- Open browser: http://localhost:8080
- You should see JSON response with app name and status
- If not, backend is not running

#### 2. Verify Frontend Proxy Configuration

**File: frontend/vite.config.ts**

The proxy MUST point to port 8080:
\\\	ypescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',  // MUST BE 8080
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
\\\

**What this does:**
- Frontend on localhost:3000 intercepts /api/* requests
- Rewrites them to http://localhost:8080/* (removes /api prefix)
- Returns response to frontend

#### 3. Verify CORS Configuration

**File: backend/config.py**

CORS origins must include the frontend URL:
\\\python
cors_origins: str = "http://localhost:5173,http://localhost:3000"
\\\

#### 4. Browser Console Debugging

**Steps:**
1. Open Frontend: http://localhost:3000
2. Open Browser DevTools (F12)
3. Go to Network tab
4. Try to trigger an API call (e.g., login)
5. Look for failed requests

#### 5. Setup Summary

**Terminal 1 (Backend):**
\\\powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8080
\\\

**Terminal 2 (Frontend):**
\\\powershell
cd frontend
npm run dev
\\\

**Access Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080

### Troubleshooting Checklist

- [ ] Backend running on port 8080? Check http://localhost:8080/health
- [ ] Frontend running on port 3000? Check http://localhost:3000
- [ ] Frontend vite.config.ts proxy target is http://localhost:8080?
- [ ] Backend CORS includes http://localhost:3000?
- [ ] No other services using ports 3000 or 8080?
- [ ] Virtual environment activated in backend terminal?
- [ ] All required .env variables set?

