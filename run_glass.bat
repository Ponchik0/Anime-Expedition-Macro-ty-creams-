@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python main.py --glass %*
    set RUN_EXIT=%errorlevel%
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py main.py --glass %*
        set RUN_EXIT=%errorlevel%
    ) else (
        echo Python not found on PATH. Install Python from python.org and try again.
        pause
        endlocal
        exit /b 1
    )
)

if not "%RUN_EXIT%"=="0" (
    echo.
    echo main.py exited with an error ^(code %RUN_EXIT%^).
    pause
)

endlocal
