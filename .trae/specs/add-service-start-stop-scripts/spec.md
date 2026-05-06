# 服务启动停止脚本 Spec

## Why
当前项目需要手动使用 Python 命令启动服务，缺乏便捷的启动/停止脚本。需要在 bin 目录下提供标准化的启动和停止脚本，支持 Windows 和 Linux 平台，包含进程检查和自动重启逻辑。

## What Changes
- 创建 bin 目录
- 创建 start.bat（Windows启动脚本）
- 创建 stop.bat（Windows停止脚本）
- 创建 start.sh（Linux启动脚本）
- 创建 stop.sh（Linux停止脚本）
- 更新 AGENTS.md 和 design.md 文档

## Impact
- Affected specs: define-local-deployment
- Affected code: 无代码变更，新增脚本文件

## ADDED Requirements

### Requirement: Windows启动脚本
系统 SHALL 提供 Windows 平台的启动脚本 start.bat。

#### Scenario: 进程检查与重启
- **WHEN** 用户执行 start.bat
- **THEN** 脚本检查是否存在运行中的进程（通过端口或进程名）
- **AND** 如果存在运行进程，先停止旧进程
- **AND** 启动新进程并输出启动信息

#### Scenario: 端口配置
- **WHEN** 用户执行 start.bat
- **THEN** 脚本使用默认端口 8080，或通过参数指定端口

### Requirement: Windows停止脚本
系统 SHALL 提供 Windows 平台的停止脚本 stop.bat。

#### Scenario: 进程停止
- **WHEN** 用户执行 stop.bat
- **THEN** 脚本检查并停止运行中的进程
- **AND** 输出停止状态信息

#### Scenario: 无进程运行
- **WHEN** 用户执行 stop.bat 且无进程运行
- **THEN** 脚本输出"无运行进程"提示

### Requirement: Linux启动脚本
系统 SHALL 提供 Linux 平台的启动脚本 start.sh。

#### Scenario: 进程检查与重启
- **WHEN** 用户执行 start.sh
- **THEN** 脚本检查是否存在运行中的进程（通过端口或进程名）
- **AND** 如果存在运行进程，先停止旧进程
- **AND** 启动新进程并输出启动信息

#### Scenario: 权限设置
- **WHEN** 脚本文件创建
- **THEN** 脚本具有可执行权限（chmod +x）

### Requirement: Linux停止脚本
系统 SHALL 提供 Linux 平台的停止脚本 stop.sh。

#### Scenario: 进程停止
- **WHEN** 用户执行 stop.sh
- **THEN** 脚本检查并停止运行中的进程
- **AND** 输出停止状态信息

### Requirement: 进程标识
系统 SHALL 使用统一的进程标识方式。

#### Scenario: Windows进程标识
- **WHEN** 在 Windows 平台检查进程
- **THEN** 使用端口（默认8080）查找进程，或使用进程名"python"配合命令行参数识别

#### Scenario: Linux进程标识
- **WHEN** 在 Linux 平台检查进程
- **THEN** 使用 PID 文件（bin/dte-diag.pid）或端口查找进程

### Requirement: 文档更新
系统 SHALL 更新项目文档反映新增的脚本功能。

#### Scenario: AGENTS.md更新
- **WHEN** 脚本创建完成
- **THEN** AGENTS.md 增加 bin 目录和启动脚本说明章节

#### Scenario: design.md更新
- **WHEN** 脚本创建完成
- **THEN** design.md 增加部署脚本使用说明

---

## 详细设计

### 1. 目录结构

```
bin/
├── start.bat    # Windows启动脚本
├── stop.bat     # Windows停止脚本
├── start.sh     # Linux启动脚本
├── stop.sh      # Linux停止脚本
└── dte-diag.pid # PID文件（Linux运行时生成）
```

### 2. start.bat 设计

```batch
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
```

### 3. stop.bat 设计

```batch
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
```

### 4. start.sh 设计

```bash
#!/bin/bash
# DTE Diagnostic Agent Start Script for Linux
# Usage: ./start.sh [port]

set -e

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHONPATH="${PROJECT_ROOT}/src"
PID_FILE="${PROJECT_ROOT}/bin/dte-diag.pid"

# 设置端口（默认8080）
PORT=${1:-8080}

# 设置配置文件
CONFIG="${PROJECT_ROOT}/config.yaml"

# 检查端口是否被占用
echo "Checking port ${PORT}..."
EXISTING_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
if [ -n "${EXISTING_PID}" ]; then
    echo "Found process using port ${PORT}, PID: ${EXISTING_PID}"
    kill ${EXISTING_PID} 2>/dev/null || true
    sleep 2
    echo "Killed existing process"
fi

# 检查 PID 文件
if [ -f "${PID_FILE}" ]; then
    OLD_PID=$(cat "${PID_FILE}")
    if ps -p ${OLD_PID} > /dev/null 2>&1; then
        echo "Stopping existing process from PID file: ${OLD_PID}"
        kill ${OLD_PID} 2>/dev/null || true
        sleep 2
    fi
    rm -f "${PID_FILE}"
fi

# 启动服务
echo "Starting DTE Diagnostic Agent on port ${PORT}..."
cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}/src"
nohup python -m dte_diagnostic_agent --config "${CONFIG}" --port ${PORT} > "${PROJECT_ROOT}/logs/agent.log" 2>&1 &
NEW_PID=$!

# 写入 PID 文件
echo ${NEW_PID} > "${PID_FILE}"

echo "Service started successfully on port ${PORT}"
echo "PID: ${NEW_PID}"
echo "PID file: ${PID_FILE}"
echo "Access API at http://localhost:${PORT}/docs"
```

### 5. stop.sh 设计

```bash
#!/bin/bash
# DTE Diagnostic Agent Stop Script for Linux
# Usage: ./stop.sh [port]

set -e

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="${PROJECT_ROOT}/bin/dte-diag.pid"

# 设置端口（默认8080）
PORT=${1:-8080}

# 停止进程函数
stop_process() {
    local PID=$1
    echo "Stopping process ${PID}..."
    kill ${PID} 2>/dev/null || true
    sleep 2
    
    # 检查是否需要强制停止
    if ps -p ${PID} > /dev/null 2>&1; then
        echo "Process still running, forcing kill..."
        kill -9 ${PID} 2>/dev/null || true
    fi
}

# 通过 PID 文件停止
if [ -f "${PID_FILE}" ]; then
    PID=$(cat "${PID_FILE}")
    if ps -p ${PID} > /dev/null 2>&1; then
        stop_process ${PID}
        echo "Process stopped from PID file"
    else
        echo "PID file exists but process not running"
    fi
    rm -f "${PID_FILE}"
fi

# 通过端口查找并停止
EXISTING_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
if [ -n "${EXISTING_PID}" ]; then
    stop_process ${EXISTING_PID}
    echo "Process stopped from port ${PORT}"
fi

# 检查结果
FINAL_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
if [ -z "${FINAL_PID}" ]; then
    echo "No process running on port ${PORT}"
else
    echo "Warning: Process still running on port ${PORT}, PID: ${FINAL_PID}"
fi
```

### 6. AGENTS.md 新增章节

在 AGENTS.md 第8节"启动入口"后新增：

```markdown
---

## 9. 启动脚本 (bin/)

### 9.1 Windows脚本

**start.bat** - 启动服务
```batch
start.bat [port]
```
- 默认端口: 8080
- 自动检测并重启已有进程

**stop.bat** - 停止服务
```batch
stop.bat [port]
```
- 通过端口查找并停止进程

### 9.2 Linux脚本

**start.sh** - 启动服务
```bash
./start.sh [port]
```
- 默认端口: 8080
- PID文件: bin/dte-diag.pid
- 日志输出: logs/agent.log

**stop.sh** - 停止服务
```bash
./stop.sh [port]
```
- 通过PID文件或端口停止进程
```

### 7. design.md 新增内容

在部署章节增加脚本使用说明。