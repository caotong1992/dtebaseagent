@echo off
REM DTE Diagnostic Agent Start Script for Windows
REM Usage: start.bat [port] [--restart|-r]

setlocal enabledelayedexpansion

REM Set project root directory
set PROJECT_ROOT=%~dp0..
set PYTHONPATH=%PROJECT_ROOT%\src
set PID_FILE=%PROJECT_ROOT%\bin\dte-diag.pid

REM Default values
set PORT=8080
set FORCE_RESTART=0

REM Parse parameters
:parse_args
if "%1"=="" goto :end_parse
if "%1"=="--restart" (
    set FORCE_RESTART=1
    shift
    goto :parse_args
)
if "%1"=="-r" (
    set FORCE_RESTART=1
    shift
    goto :parse_args
)
set PORT=%1
shift
goto :parse_args
:end_parse

REM Set config file
set CONFIG=%PROJECT_ROOT%\config.yaml

echo ========================================
echo DTE Diagnostic Agent Start Script
echo ========================================
echo Port: %PORT%
echo Config: %CONFIG%
echo PID File: %PID_FILE%
echo Force Restart: %FORCE_RESTART%
echo ========================================

REM Step 1: If force restart, stop existing process immediately
if %FORCE_RESTART% equ 1 (
    echo Force restart requested...
    
    REM Stop process from PID file
    if exist "%PID_FILE%" (
        for /f "usebackq" %%i in ("%PID_FILE%") do set OLD_PID=%%i
        if defined OLD_PID (
            echo Stopping process from PID file: !OLD_PID!
            taskkill /F /PID !OLD_PID! >nul 2>&1
        )
        del "%PID_FILE%" >nul 2>&1
    )
    
    REM Stop any process on the port
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
        set PORT_PID=%%a
        echo Stopping process on port %PORT%, PID: !PORT_PID!
        taskkill /F /PID !PORT_PID! >nul 2>&1
    )
    
    echo Old processes stopped
    goto :start_service
)

REM Step 2: Normal start - check if PID file exists
set OLD_PID=
if exist "%PID_FILE%" (
    echo Checking PID file...
    type "%PID_FILE%" >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "usebackq" %%i in ("%PID_FILE%") do set OLD_PID=%%i
        echo Old PID from file: !OLD_PID!
        
        if defined OLD_PID (
            REM Check if process is running
            tasklist 2>nul | findstr "!OLD_PID!" >nul
            if !errorlevel! equ 0 (
                echo Process !OLD_PID! is still running
                
                REM Check if using same port
                netstat -aon 2>nul | findstr ":%PORT%" | findstr "LISTENING" | findstr "!OLD_PID!" >nul
                if !errorlevel! equ 0 (
                    echo ========================================
                    echo Same process is running on port %PORT%
                    echo PID: !OLD_PID!
                    echo Skipping restart
                    echo ========================================
                    goto :end
                )
                
                echo Process exists but not on port %PORT%, stopping...
                taskkill /F /PID !OLD_PID! >nul 2>&1
            ) else (
                echo Process !OLD_PID! not found, cleaning PID file
            )
            del "%PID_FILE%" >nul 2>&1
        )
    )
)

REM Step 3: Check if port is occupied by unknown process
echo Checking port %PORT%...
set PORT_PID=
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set PORT_PID=%%a
)
if defined PORT_PID (
    echo Found unknown process on port %PORT%, PID: !PORT_PID!
    taskkill /F /PID !PORT_PID! >nul 2>&1
    echo Killed unknown process
)

:start_service
REM Step 4: Start new service
echo ========================================
echo Starting DTE Diagnostic Agent...
echo ========================================
cd /d %PROJECT_ROOT%
start "DTE Diagnostic Agent" python -m dte_diagnostic_agent --config %CONFIG% --port %PORT%

REM Wait for service to start
echo Waiting for service to start...
ping -n 4 127.0.0.1 >nul

REM Step 5: Save new PID
set NEW_PID=
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set NEW_PID=%%a
)

if defined NEW_PID (
    echo !NEW_PID!> "%PID_FILE%"
    echo ========================================
    echo Service started successfully!
    echo PID: !NEW_PID!
    echo PID saved to: %PID_FILE%
    echo ========================================
) else (
    echo Warning: Could not find process PID
)

echo Access API at http://localhost:%PORT%/docs

:end
endlocal