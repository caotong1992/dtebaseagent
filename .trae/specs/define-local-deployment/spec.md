# 本地单机部署方案 Spec

## Why
简化系统部署复杂度，采用本地单机部署方案替代容器化部署，移除Kubernetes相关依赖和状态监控能力，适用于小规模运维场景和快速验证需求。

## What Changes
- 移除容器化部署方案（Kubernetes Deployment、Service、ConfigMap等）
- 移除Dockerfile容器构建配置
- 移除Agent状态监控能力（Prometheus指标、告警规则）
- 定义本地单机部署方案（systemd服务、进程管理）
- 简化配置管理方式
- 移除多实例负载均衡需求

## Impact
- Affected specs: 部署架构、监控告警章节
- Affected code: deployment/目录、监控相关代码、启动脚本

## ADDED Requirements

### Requirement: 本地单机部署配置
系统 SHALL 提供本地单机部署方案，支持通过systemd服务或直接命令启动。

#### Scenario: systemd服务启动
- **WHEN** 用户执行 systemctl start dte-diagnostic-agent
- **THEN** 服务作为后台进程启动并运行

#### Scenario: 直接命令启动
- **WHEN** 用户执行 python -m dte_diagnostic_agent
- **THEN** 服务在前台启动并监听指定端口

#### Scenario: 配置文件加载
- **WHEN** 服务启动时
- **THEN** 从本地配置文件（config.yaml）加载配置

### Requirement: 本地配置管理
系统 SHALL 使用本地YAML配置文件管理所有配置项。

#### Scenario: 配置文件位置
- **WHEN** 服务启动时查找配置文件
- **THEN** 优先使用命令行指定路径，其次使用/etc/dte-diagnostic-agent/config.yaml，最后使用~/.dte-diag/config.yaml

#### Scenario: 配置验证
- **WHEN** 配置文件加载失败
- **THEN** 服务报错退出并提示配置文件问题

### Requirement: 进程管理
系统 SHALL 支持基本的进程启动、停止和重启操作。

#### Scenario: 停止服务
- **WHEN** 用户执行 systemctl stop dte-diagnostic-agent 或 Ctrl+C
- **THEN** 服务优雅关闭，释放资源

#### Scenario: 重启服务
- **WHEN** 用户执行 systemctl restart dte-diagnostic-agent
- **THEN** 服务先停止再重新启动

## MODIFIED Requirements

### Requirement: 部署架构（原design.md第10节）
部署方案从容器化部署改为本地单机部署。

原部署方案：
```
生产环境部署: Kubernetes Deployment + Service + ConfigMap
容器化: Dockerfile + docker-compose
```

修改后部署方案：
```
本地单机部署: systemd服务 + 直接命令启动
配置管理: 本地YAML配置文件
进程管理: systemctl 或 命令行
```

## REMOVED Requirements

### Requirement: Kubernetes部署配置
**Reason**: 采用本地单机部署，无需容器编排能力
**Migration**: 使用systemd服务替代K8s Deployment管理进程

### Requirement: Dockerfile容器构建
**Reason**: 本地部署无需容器化
**Migration**: 直接使用Python运行环境启动服务

### Requirement: Prometheus监控指标
**Reason**: 移除Agent状态监控能力，简化系统
**Migration**: 用户可通过健康检查接口判断服务状态

### Requirement: Grafana监控面板
**Reason**: 移除Agent状态监控能力
**Migration**: 无替代，用户不需要监控面板

### Requirement: 告警规则配置
**Reason**: 移除Agent状态监控能力
**Migration**: 无替代，用户不需要告警规则

### Requirement: 多实例负载均衡
**Reason**: 本地单机部署，单实例运行
**Migration**: 无替代，仅支持单实例

---

## 详细本地部署设计

### 1. systemd服务配置

**服务文件位置**: `/etc/systemd/system/dte-diagnostic-agent.service`

```ini
[Unit]
Description=DTEBaseService Diagnostic Agent
After=network.target

[Service]
Type=simple
User=dte-agent
Group=dte-agent
WorkingDirectory=/opt/dte-diagnostic-agent
ExecStart=/usr/bin/python3.14 -m dte_diagnostic_agent --config /etc/dte-diagnostic-agent/config.yaml
ExecStop=/bin/kill -TERM $MAINPID
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. 启动命令

**命令行启动**:
```bash
# 前台启动（开发调试）
python3.14 -m dte_diagnostic_agent

# 指定配置文件
python3.14 -m dte_diagnostic_agent --config /path/to/config.yaml

# 指定端口
python3.14 -m dte_diagnostic_agent --port 8080

# 指定API密钥
python3.14 -m dte_diagnostic_agent --api-key your-api-key
```

**systemd管理**:
```bash
# 启动服务
sudo systemctl start dte-diagnostic-agent

# 停止服务
sudo systemctl stop dte-diagnostic-agent

# 重启服务
sudo systemctl restart dte-diagnostic-agent

# 查看状态
sudo systemctl status dte-diagnostic-agent

# 查看日志
sudo journalctl -u dte-diagnostic-agent -f

# 开机自启
sudo systemctl enable dte-diagnostic-agent
```

### 3. 配置文件结构

**配置文件位置**: `/etc/dte-diagnostic-agent/config.yaml` 或 `~/.dte-diag/config.yaml`

```yaml
# 服务配置
server:
  host: 0.0.0.0
  port: 8080
  workers: 1

# OpenAI API配置
llm:
  api_key: your-openai-api-key
  base_url: https://api.openai.com/v1  # 可选，用于自定义API地址
  model_name: gpt-4o
  temperature: 0.1
  max_iterations: 15

# 数据存储配置（本地文件）
storage:
  session_dir: /var/lib/dte-diagnostic-agent/sessions
  case_dir: /var/lib/dte-diagnostic-agent/cases
  log_dir: /var/log/dte-diagnostic-agent

# 日志配置
logging:
  level: INFO
  file: /var/log/dte-diagnostic-agent/agent.log
  max_size: 10MB
  backup_count: 5

# API认证配置
auth:
  api_keys:
    - your-api-key-1
    - your-api-key-2
  # 可选：从环境变量读取
  # env_key: DTE_DIAG_API_KEY

# 集群连接配置（预定义）
clusters:
  prod-01:
    kubeconfig: /path/to/kubeconfig-prod-01
    ssh_key: ~/.ssh/id_rsa_prod
  prod-02:
    kubeconfig: /path/to/kubeconfig-prod-02
    ssh_key: ~/.ssh/id_rsa_prod
  dev-01:
    kubeconfig: null
    ssh_key: ~/.ssh/id_rsa_dev
```

### 4. 目录结构

```
/opt/dte-diagnostic-agent/          # 应用安装目录
├── src/
│   └── dte_diagnostic_agent/
├── config.yaml                      # 默认配置
└── requirements.txt

/etc/dte-diagnostic-agent/           # 系统配置目录
├── config.yaml                      # 主配置文件
└── api-keys.yaml                    # API密钥配置（可选）

/var/lib/dte-diagnostic-agent/       # 数据目录
├── sessions/                        # 诊断会话数据
├── cases/                           # 案例库数据
└── vector_store/                    # 向量存储数据

/var/log/dte-diagnostic-agent/       # 日志目录
├── agent.log                        # 主日志
└── error.log                        # 错误日志
```

### 5. 安装脚本

**install.sh**:
```bash
#!/bin/bash

INSTALL_DIR="/opt/dte-diagnostic-agent"
CONFIG_DIR="/etc/dte-diagnostic-agent"
DATA_DIR="/var/lib/dte-diagnostic-agent"
LOG_DIR="/var/log/dte-diagnostic-agent"

# 创建目录
mkdir -p $INSTALL_DIR $CONFIG_DIR $DATA_DIR $LOG_DIR
mkdir -p $DATA_DIR/sessions $DATA_DIR/cases $DATA_DIR/vector_store

# 复制应用文件
cp -r src $INSTALL_DIR/
cp requirements.txt $INSTALL_DIR/

# 安装依赖
pip install -r $INSTALL_DIR/requirements.txt

# 复制配置文件
cp config.yaml.example $CONFIG_DIR/config.yaml

# 创建用户
useradd -r -d $DATA_DIR -s /bin/bash dte-agent

# 设置权限
chown -R dte-agent:dte-agent $DATA_DIR $LOG_DIR
chmod 750 $DATA_DIR $LOG_DIR

# 安装systemd服务
cp systemd/dte-diagnostic-agent.service /etc/systemd/system/
systemctl daemon-reload

echo "安装完成！"
echo "请编辑 $CONFIG_DIR/config.yaml 配置文件"
echo "然后执行 systemctl start dte-diagnostic-agent 启动服务"
```

### 6. 启动参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | ~/.dte-diag/config.yaml |
| `--port` | 服务监听端口 | 8080 |
| `--host` | 服务监听地址 | 0.0.0.0 |
| `--api-key` | API认证密钥（可覆盖配置） | 从配置文件读取 |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | 从配置文件读取 |
| `--workers` | 工作进程数（单机部署固定为1） | 1 |
| `--dry-run` | 仅验证配置不启动服务 | false |

### 7. 健康检查

服务启动后可通过以下方式检查状态：

```bash
# HTTP健康检查
curl http://localhost:8080/api/v1/health

# systemd状态检查
systemctl status dte-diagnostic-agent

# 进程检查
ps aux | grep dte_diagnostic_agent

# 日志检查
tail -f /var/log/dte-diagnostic-agent/agent.log
```

### 8. 优雅关闭

服务收到SIGTERM信号时：
1. 停止接收新请求
2. 等待现有请求完成（最长30秒）
3. 关闭数据库连接和SSH会话
4. 保存未完成的诊断状态
5. 退出进程