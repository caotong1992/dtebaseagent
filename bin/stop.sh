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