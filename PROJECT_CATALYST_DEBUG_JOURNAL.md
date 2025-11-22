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
*   **STATUS: RESOLVED.** The `401 Unauthorized` error is no longer occurring.

**Root Causes Identified & Fixed:**
1.  **Deprecated `datetime.utcnow()` usage:** The backend used `datetime.utcnow()` which caused JWT serialization/comparison issues. **Fix:** Replaced with `datetime.now(timezone.utc)`.
2.  **JWT Secret Key Whitespace Mismatch:** Trailing whitespace in `.env` caused encoding/decoding mismatch. **Fix:** Added a Pydantic `field_validator` in `config.py` to strip whitespace from `jwt_secret_key`.
3.  **Insufficient Error Logging:** Minimal logging made JWT decoding failures difficult to diagnose. **Fix:** Added comprehensive logging throughout the JWT validation process.
4.  **Incorrect Subject (`sub`) Claim Type:** The `python-jose` library required the `sub` claim in the JWT payload to be a string, but the application was creating it as an integer (`user.id`). **Fix:** The `create_access_token` function in `backend/routers/auth.py` was modified to explicitly convert the `user.id` to a string (`str(user.id)`) when creating the JWT.

**Files Involved in Fixes:**
- `backend/routers/auth.py`
- `backend/config.py`

**Final Confirmation:** All `401 Unauthorized` issues are resolved.
