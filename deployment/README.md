# 本地单机部署配置说明

## 配置文件概述

DTE Diagnostic Agent 使用 YAML 格式的配置文件管理所有配置项。

### 配置文件位置

服务启动时按以下顺序查找配置文件：

1. 命令行指定路径（`--config` 参数）
2. `/etc/dte-diagnostic-agent/config.yaml`（系统配置）
3. `~/.dte-diag/config.yaml`（用户配置）

## 配置项说明

### server - 服务配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | string | `0.0.0.0` | 服务监听地址 |
| `port` | int | `8080` | 服务监听端口 |
| `workers` | int | `1` | 工作进程数（单机部署固定为1） |

```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 1
```

### llm - OpenAI API 配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `api_key` | string | 是 | OpenAI API 密钥 |
| `base_url` | string | 否 | API 基础地址，默认为 OpenAI 官方地址 |
| `model_name` | string | 是 | 使用的模型名称 |
| `temperature` | float | 否 | 生成温度，范围 0.0-2.0，默认 0.1 |
| `max_iterations` | int | 否 | Agent 最大迭代次数，默认 15 |

```yaml
llm:
  api_key: sk-xxx
  base_url: https://api.openai.com/v1
  model_name: gpt-4o
  temperature: 0.1
  max_iterations: 15
```

### storage - 数据存储配置

| 参数 | 类型 | 说明 |
|------|------|------|
| `session_dir` | string | 诊断会话数据存储目录 |
| `case_dir` | string | 案例库数据存储目录 |
| `log_dir` | string | 日志文件存储目录 |

```yaml
storage:
  session_dir: /var/lib/dte-diagnostic-agent/sessions
  case_dir: /var/lib/dte-diagnostic-agent/cases
  log_dir: /var/log/dte-diagnostic-agent
```

### logging - 日志配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | string | `INFO` | 日志级别：DEBUG/INFO/WARNING/ERROR |
| `file` | string | - | 日志文件路径 |
| `max_size` | string | `10MB` | 单个日志文件最大大小 |
| `backup_count` | int | `5` | 保留的历史日志文件数量 |

```yaml
logging:
  level: INFO
  file: /var/log/dte-diagnostic-agent/agent.log
  max_size: 10MB
  backup_count: 5
```

### auth - API 认证配置

| 参数 | 类型 | 说明 |
|------|------|------|
| `api_keys` | list | API 密钥列表，用于请求认证 |
| `env_key` | string | 环境变量名称，从环境变量读取密钥 |

```yaml
auth:
  api_keys:
    - your-api-key-1
    - your-api-key-2
  env_key: DTE_DIAG_API_KEY
```

### clusters - 集群连接配置

预定义的集群连接信息，支持多个集群配置。

| 参数 | 类型 | 说明 |
|------|------|------|
| `kubeconfig` | string | kubeconfig 文件路径，`null` 表示不使用 |
| `ssh_key` | string | SSH 私钥文件路径 |

```yaml
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

## 完整配置示例

```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 1

llm:
  api_key: your-openai-api-key
  base_url: https://api.openai.com/v1
  model_name: gpt-4o
  temperature: 0.1
  max_iterations: 15

storage:
  session_dir: /var/lib/dte-diagnostic-agent/sessions
  case_dir: /var/lib/dte-diagnostic-agent/cases
  log_dir: /var/log/dte-diagnostic-agent

logging:
  level: INFO
  file: /var/log/dte-diagnostic-agent/agent.log
  max_size: 10MB
  backup_count: 5

auth:
  api_keys:
    - your-api-key-1
    - your-api-key-2
  env_key: DTE_DIAG_API_KEY

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

## 启动参数覆盖

以下命令行参数可覆盖配置文件设置：

| 参数 | 说明 |
|------|------|
| `--config` | 指定配置文件路径 |
| `--port` | 覆盖服务端口 |
| `--host` | 覆盖监听地址 |
| `--api-key` | 覆盖 API 认证密钥 |
| `--log-level` | 覆盖日志级别 |
| `--log-file` | 覆盖日志文件路径 |
| `--workers` | 覆盖工作进程数 |
| `--dry-run` | 仅验证配置不启动服务 |

## 配置验证

启动前可使用 `--dry-run` 参数验证配置：

```bash
python -m dte_diagnostic_agent --config config.yaml --dry-run
```

配置验证失败时，服务将报错退出并提示具体问题。