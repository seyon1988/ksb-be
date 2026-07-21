@echo off
echo Terminating KSB Backend process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Terminating PID: %%a
    taskkill /F /PID %%a 2>nul
)
echo KSB Backend terminated successfully.
timeout /t 3
