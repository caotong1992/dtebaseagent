#!/bin/bash
# DTE Diagnostic Agent Start Script for Linux
# Usage: ./start.sh [port]

set -e

# 设置项目根目录
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
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

# 确保 logs 目录存在
mkdir -p "${PROJECT_ROOT}/logs"

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