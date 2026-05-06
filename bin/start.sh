#!/bin/bash
# DTE Diagnostic Agent Start Script for Linux
# Usage: ./start.sh [port] [--restart|-r]

set -e

# Set project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHONPATH="${PROJECT_ROOT}/src"
PID_FILE="${PROJECT_ROOT}/bin/dte-diag.pid"

# Default values
PORT=8080
FORCE_RESTART=false

# Parse parameters
while [[ $# -gt 0 ]]; do
    case $1 in
        --restart|-r)
            FORCE_RESTART=true
            shift
            ;;
        *)
            PORT=$1
            shift
            ;;
    esac
done

# Set config file
CONFIG="${PROJECT_ROOT}/config.yaml"

echo "========================================"
echo "DTE Diagnostic Agent Start Script"
echo "========================================"
echo "Port: ${PORT}"
echo "Config: ${CONFIG}"
echo "PID File: ${PID_FILE}"
echo "Force Restart: ${FORCE_RESTART}"
echo "========================================"

# Step 1: If force restart, stop existing process immediately
if [ "${FORCE_RESTART}" = "true" ]; then
    echo "Force restart requested..."
    
    # Stop process from PID file
    if [ -f "${PID_FILE}" ]; then
        OLD_PID=$(cat "${PID_FILE}")
        if [ -n "${OLD_PID}" ]; then
            echo "Stopping process from PID file: ${OLD_PID}"
            kill ${OLD_PID} 2>/dev/null || true
            sleep 1
        fi
        rm -f "${PID_FILE}"
    fi
    
    # Stop any process on the port
    PORT_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
    if [ -n "${PORT_PID}" ]; then
        echo "Stopping process on port ${PORT}, PID: ${PORT_PID}"
        kill ${PORT_PID} 2>/dev/null || true
        sleep 1
    fi
    
    echo "Old processes stopped"
else
    # Step 2: Normal start - check if PID file exists
    if [ -f "${PID_FILE}" ]; then
        echo "Checking PID file..."
        OLD_PID=$(cat "${PID_FILE}")
        if [ -n "${OLD_PID}" ]; then
            echo "Old PID from file: ${OLD_PID}"
            
            # Check if process is running
            if ps -p ${OLD_PID} > /dev/null 2>&1; then
                echo "Process ${OLD_PID} is still running"
                
                # Check if using same port
                PORT_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
                if [ "${PORT_PID}" = "${OLD_PID}" ]; then
                    echo "========================================"
                    echo "Same process is running on port ${PORT}"
                    echo "PID: ${OLD_PID}"
                    echo "Skipping restart"
                    echo "========================================"
                    exit 0
                fi
                
                echo "Process exists but not on port ${PORT}, stopping..."
                kill ${OLD_PID} 2>/dev/null || true
                sleep 1
            else
                echo "Process ${OLD_PID} not found, cleaning PID file"
            fi
            rm -f "${PID_FILE}"
        fi
    fi
    
    # Step 3: Check if port is occupied by unknown process
    echo "Checking port ${PORT}..."
    PORT_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
    if [ -n "${PORT_PID}" ]; then
        echo "Found unknown process on port ${PORT}, PID: ${PORT_PID}"
        kill ${PORT_PID} 2>/dev/null || true
        sleep 1
        echo "Killed unknown process"
    fi
fi

# Ensure logs directory exists
mkdir -p "${PROJECT_ROOT}/logs"

# Step 4: Start new service
echo "========================================"
echo "Starting DTE Diagnostic Agent..."
echo "========================================"
cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}/src"
nohup python -m dte_diagnostic_agent --config "${CONFIG}" --port ${PORT} > "${PROJECT_ROOT}/logs/agent.log" 2>&1 &
NEW_PID=$!

# Wait for service to start
sleep 3

# Verify service started
PORT_PID=$(lsof -t -i:${PORT} 2>/dev/null || true)
if [ -n "${PORT_PID}" ]; then
    echo ${PORT_PID} > "${PID_FILE}"
    echo "========================================"
    echo "Service started successfully!"
    echo "PID: ${PORT_PID}"
    echo "PID saved to: ${PID_FILE}"
    echo "========================================"
else
    echo "Warning: Could not find process on port ${PORT}"
fi

echo "Access API at http://localhost:${PORT}/docs"