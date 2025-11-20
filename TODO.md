# Catalyst Project: To-Do List

This document outlines the remaining tasks to complete the Catalyst project.

## Frontend (`/frontend`)

The frontend is mostly complete, but requires the following integrations:

- [ ] **Implement Hume AI Voice Integration:**
  - The current voice input is a placeholder (`App.tsx`).
  - **Task:** Integrate the Hume AI SDK to enable real-time voice capture and emotional analysis. Update the `handleVoiceToggle` function to use the SDK.

- [ ] **Implement Conversation History Panel:**
  - The "History" button in the header is currently inactive.
  - **Task:** Create a side panel or view that lists past conversations.
  - **Details:**
    - Fetch conversation summaries using the `api.listConversations()` function.
    - Allow the user to select a conversation to view its messages.
    - Implement conversation deletion using `api.deleteConversation()`.

## Backend (`/backend`)

The backend has a solid structure, but the core AI and authentication logic needs to be implemented.

- [ ] **Add AI Provider Libraries:**
  - The `requirements.txt` file is missing the necessary Python libraries for the AI models.
  - **Task:** Add the following libraries to `requirements.txt`:
    - `google-generativeai` (for Gemini)
    - `anthropic` (for Claude)
    - `deepseek-python` (or the relevant library for DeepSeek)

- [ ] **Implement AI Router & Providers:**
  - This is the highest priority task.
  - **Task:** Create the AI routing logic as detailed in `improvement_suggestions.txt`.
  - **Details:**
    - Create a `backend/services/ai_router.py` file to house the `AIRouter` class.
    - Create provider classes (e.g., `GeminiProvider`, `ClaudeProvider`) in a `backend/services/providers/` directory.
    - These providers will handle the actual API calls to the different AI models.

- [ ] **Complete API Routers:**
  - The `conversations` and `synthesis` routers need to be updated to use the `AIRouter`.
  - **Task:**
    - In `backend/routers/conversations.py`, modify the message creation endpoint to call the `AIRouter` to get an AI-generated response.
    - In `backend/routers/synthesis.py`, implement the logic for the weekly "Connect the Dots" synthesis using the most powerful AI (Claude).

- [ ] **Implement Authentication:**
  - The project requires authentication to protect user data.
  - **Task:** Implement a JWT-based authentication system.
  - **Details:**
    - Create endpoints for user registration and login (e.g., `/auth/register`, `/auth/token`).
    - Secure the API endpoints to require a valid JWT.
    - Integrate Google OAuth 2.0 for user sign-in as specified in the requirements.

## API Keys & Configuration (For User)

To make the backend AI calls, you will need to add your API keys. These should be stored securely as environment variables.

- [ ] **Create a `.env` file** in the `backend` directory.
- [ ] **Add the following keys** to the `.env` file:

```env
# backend/.env

# AI Provider API Keys
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY_HERE"
DEEPSEEK_API_KEY="YOUR_DEEPSEEK_API_KEY_HERE"
HUME_API_KEY="YOUR_HUME_API_KEY_HERE"

# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID_HERE"
GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_CLIENT_SECRET_HERE"

# JWT Secret
JWT_SECRET_KEY="A_RANDOM_SECRET_STRING_FOR_ENCODING_TOKENS"
```

**Note to Developer:** The backend configuration (`backend/config.py`) will need to be updated to load these variables from the `.env` file using `pydantic-settings`.
