@echo off
REM DTE Diagnostic Agent Stop Script for Windows
REM Usage: stop.bat [port]

setlocal

REM 设置端口（默认8080）
set PORT=8080
if not "%1"=="" set PORT=%1

REM 查找并停止进程
echo Checking port %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%PORT% ^| findstr LISTENING') do (
    set PID=%%a
    echo Found process using port %PORT%, PID: %PID%
    taskkill /F /PID %PID% >nul 2>&1
    if errorlevel 1 (
        echo Failed to stop process
    ) else (
        echo Process stopped successfully
    )
    goto :end
)

echo No process found on port %PORT%

:end
endlocal