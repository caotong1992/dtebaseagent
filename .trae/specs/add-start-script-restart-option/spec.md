# Start 脚本重启能力 Spec

## Why
当前 start.bat 脚本在检测到同一进程运行时会跳过重启，用户无法强制重启服务。需要提供重启参数选项，支持强制停止现有进程并重新启动。

## What Changes
- 在 start.bat 增加 `--restart` 参数
- 在 start.sh 增加 `--restart` 参数
- 修改逻辑：当指定重启参数时，强制停止现有进程

## Impact
- Affected specs: add-service-start-stop-scripts
- Affected code: bin/start.bat, bin/start.sh

## ADDED Requirements

### Requirement: 重启参数支持
系统 SHALL 在启动脚本中支持 `--restart` 参数。

#### Scenario: 正常启动（无参数）
- **WHEN** 用户执行 start.bat 不带参数
- **THEN** 如果同一进程已运行，跳过重启
- **AND** 如果不同进程占用端口，停止旧进程后启动新进程

#### Scenario: 强制重启（带 --restart）
- **WHEN** 用户执行 start.bat --restart
- **THEN** 无论进程是否运行，强制停止现有进程
- **AND** 启动新进程

#### Scenario: 端口参数组合
- **WHEN** 用户执行 start.bat 9090 --restart
- **THEN** 停止端口 9090 上的进程并重新启动

### Requirement: Linux 脚本重启参数
系统 SHALL 在 start.sh 支持相同的重启参数。

#### Scenario: 强制重启
- **WHEN** 用户执行 ./start.sh --restart
- **THEN** 停止 PID 文件中的进程和端口上的进程
- **AND** 启动新进程

---

## 详细设计

### 1. start.bat 参数解析

```batch
REM Parse parameters
set PORT=8080
set FORCE_RESTART=0

:parse_args
if "%1"=="" goto :end_parse
if "%1"=="--restart" set FORCE_RESTART=1
if "%1"=="-r" set FORCE_RESTART=1
if not "%1"=="--restart" if not "%1"=="-r" set PORT=%1
shift
goto :parse_args
:end_parse

echo Port: %PORT%
echo Force Restart: %FORCE_RESTART%

REM If force restart, skip same-process check
if %FORCE_RESTART% equ 1 (
    echo Force restart requested, stopping existing process...
    if exist "%PID_FILE%" (
        for /f "usebackq" %%i in ("%PID_FILE%") do set OLD_PID=%%i
        if defined OLD_PID taskkill /F /PID %OLD_PID% >nul 2>&1
        del "%PID_FILE%" >nul 2>&1
    )
    goto :start_service
)

REM Normal logic: check if same process running...
```

### 2. start.sh 参数解析

```bash
PORT=8080
FORCE_RESTART=false

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

echo "Port: ${PORT}"
echo "Force Restart: ${FORCE_RESTART}"

if [ "${FORCE_RESTART}" = "true" ]; then
    echo "Force restart requested, stopping existing process..."
    # Stop existing process
    ...
fi
```

### 3. 使用方式

```batch
# Normal start (skip if same process)
start.bat

# Normal start with custom port
start.bat 9090

# Force restart
start.bat --restart

# Force restart with custom port
start.bat 9090 --restart
```