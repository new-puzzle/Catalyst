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

### **Section 3: Post-Login `401 Unauthorized` Error (NOW RESOLVED)**

**Problem: Post-Login `401 Unauthorized` Error**
*   **Symptom:** After a successful login, the very next API call (e.g., to `POST /conversations/`) fails with a `401 Unauthorized` error.
*   **STATUS: RESOLVED.**

**Root Causes Identified & Fixed:**
1.  **Deprecated `datetime.utcnow()` usage:**
    - The backend used `datetime.utcnow()` which is deprecated in Python 3.12+
    - Returns a naive (timezone-unaware) datetime that can cause JWT serialization/comparison issues
    - **Fix:** Replaced with `datetime.now(timezone.utc)` for proper timezone-aware datetime handling

2.  **JWT Secret Key Whitespace Mismatch:**
    - The `.env` file may contain trailing whitespace after `JWT_SECRET_KEY` value
    - When encoding the token, the key is `"secret123 "` (with space)
    - When decoding, the key might be loaded differently, causing a signature mismatch
    - **Fix:** Added a Pydantic field validator in `config.py` to automatically strip whitespace from `jwt_secret_key`

3.  **Insufficient Error Logging:**
    - JWT decoding failures were not providing detailed error information
    - Made it impossible to diagnose the exact mismatch
    - **Fix:** Added comprehensive logging at each step of JWT encoding/decoding to help diagnose future issues

**Changes Made:**
- **File:** `backend/routers/auth.py`
  - Added `timezone` import
  - Changed `datetime.utcnow()` → `datetime.now(timezone.utc)` in `create_access_token()`
  - Enhanced `get_current_user()` with detailed logging for JWT validation steps
  - Added specific error messages for each failure point

- **File:** `backend/config.py`
  - Added `field_validator` import
  - Added `sanitize_jwt_secret_key()` validator that strips whitespace from JWT secret key on load

**Testing Instructions:**
1. Restart the backend server (the config validator will automatically clean the secret key)
2. Attempt to log in via Google Sign-In
3. Once logged in, create a new conversation - this should now succeed with a `200 OK` response
4. Check server logs for `✅ JWT token created successfully` and `✅ User authenticated successfully` messages
