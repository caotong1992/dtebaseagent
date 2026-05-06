@echo off
REM DTE Diagnostic Agent Start Script for Windows
REM Usage: start.bat [port]

setlocal

REM 设置项目根目录
set PROJECT_ROOT=%~dp0..
set PYTHONPATH=%PROJECT_ROOT%\src

REM 设置端口（默认8080）
set PORT=8080
if not "%1"=="" set PORT=%1

REM 设置配置文件
set CONFIG=%PROJECT_ROOT%\config.yaml

REM 检查端口是否被占用
echo Checking port %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%PORT% ^| findstr LISTENING') do (
    set PID=%%a
    echo Found process using port %PORT%, PID: %PID%
    taskkill /F /PID %PID% >nul 2>&1
    echo Killed existing process
)

REM 启动服务
echo Starting DTE Diagnostic Agent on port %PORT%...
cd /d %PROJECT_ROOT%
start "DTE Diagnostic Agent" python -m dte_diagnostic_agent --config %CONFIG% --port %PORT%

echo Service started successfully on port %PORT%
echo Access API at http://localhost:%PORT%/docs

endlocal