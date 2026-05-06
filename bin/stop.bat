@echo off
REM DTE Diagnostic Agent Stop Script for Windows
REM Usage: stop.bat [port]

setlocal enabledelayedexpansion

REM Set port (default 8080)
set PORT=8080
if not "%1"=="" set PORT=%1

REM Find and stop process
echo Checking port %PORT%...
set PID=
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set PID=%%a
)

if defined PID (
    echo Found process using port %PORT%, PID: !PID!
    taskkill /F /PID !PID! >nul 2>&1
    if errorlevel 1 (
        echo Failed to stop process
    ) else (
        echo Process stopped successfully
        del "%~dp0dte-diag.pid" >nul 2>&1
        echo PID file cleaned
    )
) else (
    echo No process found on port %PORT%
)

endlocal