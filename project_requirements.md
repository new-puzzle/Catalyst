# Project: Catalyst - The AI Smart Journal

**Tech Stack:**
- **Frontend:** React (Vite), TailwindCSS, Framer Motion.
- **Backend:** Python (FastAPI).
- **Database:** SQLite (Metadata/Chat History), ChromaDB (Vector Memory).
- **AI Strategy:** Multi-AI router (Gemini Flash, DeepSeek, Claude) for cost/performance optimization.
- **Integrations:** Google OAuth 2.0 (Drive), Hume AI (Empathic Voice).

---

### 1. Core Philosophy: The Smart Journal
Catalyst is a voice-first, privacy-focused journaling companion. It uses Empathic AI (Hume) to understand the user's emotional state, bridging the gap between rambling thoughts and concrete insights. It intelligently routes tasks to different AI models to provide the best balance of speed, cost, and analytical depth.

---

### 2. The AI Provider Strategy
The system will use a router to dynamically select the best AI for a given task, with a user option to override.

- **Gemini Flash:** Default for daily journaling and quick, low-cost responses.
- **DeepSeek:** Used for `Architect` mode to structure plans and break down goals.
- **Claude:** Reserved for high-quality text generation (`Scribe` mode) and deep analysis (`Weekly Synthesis`).

This multi-AI approach provides significant cost savings (est. 70-75%) and better-tailored responses compared to a single-model architecture.

---

### 3. The "Smart Input" Interface & Modes
The UI will feature a primary voice input orb and a secondary text bar. Interaction is governed by four modes, re-interpreted for journaling:

- **✨ Auto (Default):** For daily voice journaling, quick thoughts, and empathetic listening. Powered by **Gemini Flash**.
- **🏗️ Architect:** For life planning, goal setting, and structuring ideas. Powered by **DeepSeek**.
- **🎭 Simulator:** For practicing conversations and interview prep, with real-time emotional feedback from Hume. Powered by **Claude** for nuance.
- **✍️ Scribe:** For turning journal entries or thoughts into polished assets like emails or posts. Powered by **Claude** for quality.

---

### 4. The "Neural Vault" (Backend Memory)
The memory system remains the same, with an added emphasis on tracking emotional trends over time.

- **Storage Hierarchy:**
  - `./data/db/conversations.db`: SQLite for chat history.
  - `./data/db/vector_store/`: ChromaDB for RAG on past entries and documents.
  - `./data/files/`: Synced documents from Google Drive and local uploads.
- **Ingestion Engine (RAG):**
  - **Drive Sync Job:** Background task to sync and embed Google Drive files.
  - **Emotion Logger:** Logs Hume's emotional analysis with each entry to track patterns.

---

### 5. Core Features

- **Voice Journaling:** The primary use case. Users can speak their thoughts, and the AI will respond, informed by the emotional content of their voice.
- **"Connect the Dots" (Weekly Synthesis):** A key feature that uses the most powerful AI (**Claude**) to analyze the week's journal entries, emotional data from Hume, and referenced documents. It generates a report identifying key themes, emotional patterns, progress on goals, and recurring concerns.
- **AI & Mode Selection:** The UI will allow the user to see which AI is being used and optionally override the default selection for a specific task.
- **Cost Tracking:** The system will provide visibility into monthly AI usage costs.