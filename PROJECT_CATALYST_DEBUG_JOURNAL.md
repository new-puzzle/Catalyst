### **PROJECT CATALYST - DEBUGGING JOURNAL & CURRENT STATUS**

**Objective:** This document is the complete and authoritative record of the debugging session for the Catalyst project. It is intended to prevent any AI agent from re-diagnosing solved problems or asking infuriating and redundant questions. **READ THIS BEFORE SUGGESTING ANY ACTION.**

---

### **Section 1: Core System Facts (DO NOT QUESTION)**

1.  **Project Structure:** Backend is Python/FastAPI (port 8080), Frontend is React/Vite (port 3000).
2.  **Secrets Management:** The project uses `.env` files for both frontend and backend to manage secrets. The user has confirmed these are set up.
3.  **Google Cloud Project:** **A project exists and is configured.** Do not ask if it exists. Do not ask to check the project name.
4.  **Google OAuth Client ID:** The ID is stored in `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`. It has been **verified multiple times via copy-paste** to be identical to the one configured in the Google Cloud Console. **DO NOT ask to check the Client ID again.**

---

### **Section 2: Solved Issues (DO NOT RE-DEBUG)**

**Issue A: Google Login `400 origin_mismatch` Error**
*   **Symptom:** `400 origin_mismatch` and `[GSI_LOGGER]: The given origin is not allowed...` error on login.
*   **STATUS: RESOLVED.**
*   **What DID NOT work (DO NOT SUGGEST AGAIN):** Asking to check the "Authorized JavaScript origins" in Google Cloud Console. The user confirmed 50 times that it was correctly set to `http://localhost:3000` without a trailing slash.
*   **Actual Fix:** The issue was resolved by the user performing a **hard refresh (Ctrl+Shift+R)** of the browser. It was a browser caching problem. The standing instruction is to hard-refresh if this specific error ever returns.

**Issue B: Backend Startup Crash (`AssertionError`)**
*   **Symptom:** Backend failed to start with a SQLAlchemy `AssertionError`.
*   **STATUS: RESOLVED.**
*   **Diagnosis:** A version conflict in the `venv` between `SQLAlchemy==2.0.25` and an incompatible, newer version of `typing-extensions`.
*   **Fix:** The user downgraded `typing-extensions` by running `pip install typing-extensions==4.5.0` in the venv.

**Issue C: Hume AI `400 Bad Request` Error**
*   **Symptom:** Using the voice feature previously caused `400 Bad Request` errors from the Hume AI API.
*   **STATUS: RESOLVED (for now).** The user confirmed that in recent tests, this error no longer appears. We are not actively debugging this.

---

### **Section 3: The Current & Only Active Problem**

**Problem: Post-Login `401 Unauthorized` Error**
*   **Symptom:** After a successful login, the very next API call (e.g., to `POST /conversations/`) fails with a `401 Unauthorized` error.
*   **Current Status & Key Facts:**
    1.  The frontend is working correctly. It has been **CONFIRMED** by inspecting the browser's network requests that the **`Authorization: Bearer <token>` header IS PRESENT** in the failing request.
    2.  The backend **IS LOADING THE CORRECT `JWT_SECRET_KEY`**. This was proven by adding a print statement to `main.py` which showed the correct key being loaded on server startup.
    3.  This creates a logical paradox: The backend uses the correct key to `encode` a token during login, and the frontend successfully sends it back, but the backend fails to `decode` the same token using the same key, resulting in a `401` error. The root cause for this validation failure is currently unknown.
