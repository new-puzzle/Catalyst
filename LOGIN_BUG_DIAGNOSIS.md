# LOGIN BUG - COMPLETE DIAGNOSTIC & FIX INSTRUCTIONS

## PROBLEM SUMMARY
User can log in with Google Sign-In (200 OK), but subsequent API requests fail with 401 Unauthorized. The Authorization header containing the JWT token is NOT being sent to the backend.

## ROOT CAUSE
The token is being received and stored after Google authentication, but it is not being attached to the Authorization header for subsequent API requests (like creating conversations).

## EVIDENCE FROM CONSOLE LOGS
- Line 23: OK Google Sign-In successful, token received
- Line 30: OK Backend returns 200 OK for /auth/google
- Line 33: FAIL POST /api/conversations/ returns 401 Unauthorized
- The token is successfully received (1184 chars) but not sent in subsequent requests

## WHAT NEEDS TO BE FIXED

### File 1: frontend/src/services/api.ts
ISSUE: The fetchAPI function is NOT including the Authorization header in requests

Current Problem:
1. The token is stored in localStorage as 'catalyst_token'
2. The fetchAPI function reads the token but doesn't properly attach it to headers
3. OR the token is being read at module initialization time and isn't updated when setAuthToken() is called later

What to Check:
1. Look at the fetchAPI() function
2. Check if it is setting Authorization header: "Authorization: Bearer <token>"
3. Check if it is reading from localStorage each time (not just at module init)
4. Look for all fetch() calls - they must include headers with the token

Fix Required:
- Ensure EVERY fetch request includes: headers with "Authorization": "Bearer {token}"
- Ensure the token is read from localStorage BEFORE each request, not just once at startup
- The Authorization header MUST be sent for: /conversations/, /messages/, /voice/, /synthesis/, /documents/ endpoints

### File 2: frontend/src/App.tsx
ISSUE: setAuthToken() function may not be properly updating the API module's token reference

What to Check:
1. Find the setAuthToken() function
2. Verify it sets localStorage.setItem('catalyst_token', token)
3. Verify it updates any module-level authToken variable in api.ts
4. Check that the token is actually being passed after google sign-in response

## SETUP & TESTING INSTRUCTIONS FOR AUTONOMOUS AI

### STEP 1: SETUP PYTHON VIRTUAL ENVIRONMENT
Set-Location 'C:/Users/workr/Projects/Catalyst'
python -m venv venv
.\venv\Scripts\Activate.ps1
Set-Location 'C:/Users/workr/Projects/Catalyst/backend'
pip install -r requirements.txt

### STEP 2: START BACKEND SERVER (PORT 8080)
In PowerShell window 1:
Set-Location 'C:/Users/workr/Projects/Catalyst'
.\venv\Scripts\Activate.ps1
Set-Location 'C:/Users/workr/Projects/Catalyst/backend'
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080

Expected output:
INFO:     Uvicorn running on http://0.0.0.0:8080

### STEP 3: START FRONTEND SERVER (PORT 3000)
In PowerShell window 2:
Set-Location 'C:/Users/workr/Projects/Catalyst/frontend'
npm install
npm run dev

Expected output:
VITE v5.0.8 ready
Local: http://localhost:3000/

### STEP 4: AUTONOMOUS TESTING PROCEDURE

Test 1: Backend is Running
- Open http://localhost:8080/docs
- Verify Swagger UI loads with all endpoints
- Check /auth/google, /conversations/, /messages/ visible

Test 2: Frontend is Running
- Open http://localhost:3000/
- Verify React app loads without errors in console

Test 3: API Proxy is Working
- Open DevTools (F12) â†’ Network tab
- Keep this tab open for testing

Test 4: Perform Full Login Flow
- Click "Sign in with Google"
- Use test account credentials
- Check console for: "OK Google Sign-In successful, token received"
- Check console for: "OK Backend authentication successful"

Test 5: Check Token Storage
- DevTools â†’ Application tab â†’ Local Storage
- Look for key: "catalyst_token"
- Verify token is present and has value (should be ~1184 characters)

Test 6: Monitor Network Request Headers (CRITICAL)
- In DevTools Network tab, find POST request to "conversations/"
- Click on it
- Go to Headers tab
- Look for "Authorization" header in Request Headers section
- If Authorization header is MISSING â†’ this is the bug
- If Authorization header is present â†’ bug is fixed

Test 7: Check Backend Logs for Token Validation
- Look at uvicorn terminal where backend is running
- Find POST /conversations/ request log entry
- Check if it shows 200 OK or 401 Unauthorized
- 401 = token not in header or invalid

### STEP 5: DIAGNOSIS CHECKLIST

Backend runs on 8080: Expected http://0.0.0.0:8080
Frontend runs on 3000: Expected http://localhost:3000/
Google Sign-In succeeds: Expected Console shows OK
Token stored in localStorage: Expected catalyst_token key exists
Token value length: Expected ~1184 characters
Authorization header sent: Expected Header visible in Network tab
Backend receives token: Expected 200 OK on /conversations/

### STEP 6: IF TOKEN IS NOT IN AUTHORIZATION HEADER

Then the bug is confirmed and fix is needed:

1. Open: frontend/src/services/api.ts
2. Find the fetchAPI() function
3. Look at the fetch() call - it should include Authorization header
4. The fix pattern should be:

const token = localStorage.getItem('catalyst_token');
const headers = {
  'Content-Type': 'application/json',
  'Authorization': token ? 'Bearer ' + token : ''
};

5. Verify token is read from localStorage BEFORE each request
6. Re-run Test 6 to confirm Authorization header now appears

### STEP 7: VERIFICATION AFTER FIX

After applying the fix:
1. Clear browser cache and localStorage
2. Restart frontend server: npm run dev
3. Repeat Test 4 (full login flow)
4. Repeat Test 6 (check Authorization header)
5. Confirm backend now returns 200 OK instead of 401 Unauthorized

## FILES TO INSPECT

Critical Files:
1. frontend/src/services/api.ts - CHECK fetchAPI() function
2. frontend/src/App.tsx - CHECK setAuthToken() function
3. frontend/vite.config.ts - Verify proxy config points to port 8080
4. backend/main.py - Check CORS configuration
5. backend/config.py - Check JWT validation logic

## AUTONOMOUS AI - YOUR TASK

1. Set up venv as shown above
2. Run both servers (8080 backend, 3000 frontend)
3. Perform all tests 1-7
4. Inspect api.ts and identify the exact line where Authorization header is missing
5. Fix the issue in api.ts
6. Restart frontend and re-run tests to verify fix
7. Report back with confirmation that Authorization header is now present
8. Confirm /conversations/ returns 200 OK (not 401)

DO NOT stop until login and conversation creation both succeed.
DO NOT ask user for anything.
DO NOT ask for Google Cloud Console changes.
