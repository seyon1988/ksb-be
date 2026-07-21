@echo off
echo Terminating KSB Frontend process on port 4200...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :4200 ^| findstr LISTENING') do (
    echo Terminating PID: %%a
    taskkill /F /PID %%a 2>nul
)
echo KSB Frontend terminated successfully.
timeout /t 3
