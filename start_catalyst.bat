@echo off
set "PROJECT_ROOT=C:\Users\workr\Projects\Catalyst"

echo Starting Catalyst Backend in a new command prompt window...
start "Catalyst Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8080"

echo Starting Catalyst Frontend in a new command prompt window...
start "Catalyst Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && npm run dev"

echo.
echo Catalyst backend and frontend have been launched in separate command prompt windows.
echo Please look for two new command prompt windows on your screen.
echo This script window will now close in 5 seconds.
timeout /t 5 >nul
exit
