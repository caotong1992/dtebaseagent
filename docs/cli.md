# DTE-Diag CLI 使用手册

## 概述

`dte-diag` 是 DTEBaseService 问题诊断系统的命令行工具，提供交互式诊断操作能力。通过此工具，用户可以执行诊断任务、查看诊断历史、搜索案例库、管理集群配置等操作。

## 安装方式

### 通过 pip 安装

```bash
pip install dte-diagnostic-agent
```

### 从源码安装

```bash
git clone <repository-url>
cd dtebaseagent
pip install -e .
```

### 验证安装

```bash
dte-diag --version
```

## 全局选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--config` | `-c` | 配置文件路径 | `~/.dte-diag/config.yaml` |
| `--api-url` | `-u` | API服务地址 | `http://localhost:8080` |
| `--api-key` | `-k` | API认证密钥（支持环境变量 `DTE_DIAG_API_KEY`） | - |
| `--output` | `-o` | 输出格式：`table`/`json`/`yaml`/`text`/`markdown` | `table` |
| `--verbose` | `-v` | 详细输出模式 | `false` |
| `--quiet` | `-q` | 静默模式，仅输出结果 | `false` |
| `--no-color` | - | 禁用彩色输出 | `false` |
| `--help` | `-h` | 显示帮助信息 | - |
| `--version` | - | 显示版本信息 | - |

### 示例

```bash
dte-diag -o json --verbose history --limit 5
dte-diag --api-url http://192.168.1.100:8080 cluster list
```

---

## 命令详解

### diagnose - 执行诊断

执行问题诊断任务，提交诊断请求并可选等待结果。

#### 必选参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--description` | `-d` | 问题描述 |
| `--cluster` | `-C` | 集群名称 |

#### 可选参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--node` | `-n` | 目标节点IP | - |
| `--node-user` | - | 节点登录用户 | - |
| `--node-port` | - | SSH端口 | `22` |
| `--auth-type` | - | 认证类型：`password`/`key` | - |
| `--password` | - | 登录密码 | - |
| `--ssh-key` | - | SSH密钥路径 | - |
| `--service` | `-s` | 服务名称 | `DTEBaseService` |
| `--namespace` | `-N` | K8s命名空间 | - |

#### 时间参数

| 参数 | 说明 |
|------|------|
| `--time-start` | 问题开始时间，ISO8601格式 |
| `--time-end` | 问题结束时间，ISO8601格式 |
| `--last` | 最近时间段，如：`1h`、`30m`、`2d` |

#### 诊断选项

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--priority` | - | 优先级：`critical`/`high`/`medium`/`low` | `medium` |
| `--timeout` | - | 超时时间(秒) | `300` |
| `--dry-run` | - | 仅生成诊断计划不执行 | `false` |
| `--wait` | `-w` | 等待诊断完成并显示结果 | `false` |
| `--follow` | `-f` | 实时显示诊断进度 | `false` |
| `--interactive` | `-i` | 交互式输入模式 | `false` |

#### 示例

```bash
dte-diag diagnose -d "服务响应缓慢" -C prod-01

dte-diag diagnose \
  --description "数据库连接超时，用户无法登录" \
  --cluster prod-01 \
  --node 192.168.1.100 \
  --node-user admin \
  --ssh-key ~/.ssh/id_rsa \
  --service DTEBaseService \
  --namespace production \
  --last 1h \
  --priority high \
  --wait

dte-diag diagnose -i

dte-diag diagnose -d "服务异常" -C prod-01 --dry-run
```

---

### status - 查询诊断状态

查询指定诊断会话的状态和结果。

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `session_id` | 是 | 诊断会话ID |

#### 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format` | `-F` | 输出格式：`json`/`markdown`/`text` |
| `--include-evidence` | 包含收集的证据详情 | `false` |
| `--watch` | 持续监控直到完成 | `false` |

#### 示例

```bash
dte-diag status diag-20240115-001

dte-diag status diag-20240115-001 --watch --include-evidence

dte-diag status diag-20240115-001 --format markdown
```

---

### history - 查看历史记录

查看诊断历史记录列表。

#### 选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--limit` | `-l` | 返回数量 | `20` |
| `--status` | `-s` | 状态筛选：`all`/`pending`/`running`/`completed`/`failed` | `all` |
| `--cluster` | `-C` | 集群筛选 | - |
| `--date` | - | 日期筛选 | - |
| `--after` | - | 此日期之后的记录 | - |
| `--before` | - | 此日期之前的记录 | - |

#### 示例

```bash
dte-diag history

dte-diag history --cluster prod-01 --status failed

dte-diag history --date today

dte-diag history --after "7 days ago" --status completed
```

---

### cancel - 取消诊断

取消正在运行的诊断任务。

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `session_id` | 是 | 诊断会话ID |

#### 示例

```bash
dte-diag cancel diag-20240115-001
```

---

### search - 搜索案例库

从历史案例库中搜索相关案例。

#### 必选参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--query` | `-q` | 搜索关键词 |

#### 可选参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--symptoms` | `-s` | 症状筛选，逗号分隔 | - |
| `--category` | `-c` | 问题类别筛选 | - |
| `--limit` | `-l` | 返回数量 | `10` |

#### 示例

```bash
dte-diag search --query "连接超时"

dte-diag search -q "性能问题" --symptoms "慢查询,高延迟"

dte-diag search --query "数据库" --category performance_degradation
```

---

## 案例管理命令 (case)

### case show - 查看案例详情

```bash
dte-diag case show <case_id>
```

**示例：**

```bash
dte-diag case show CASE-001
```

### case save - 保存案例

从诊断结果创建新案例。

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `session_id` | 是 | 诊断会话ID |

#### 选项

| 选项 | 简写 | 说明 |
|------|------|------|
| `--title` | `-t` | 案例标题（必填） |
| `--tags` | - | 标签，逗号分隔 |

#### 示例

```bash
dte-diag case save diag-20240115-001 \
  --title "数据库连接池耗尽解决方案" \
  --tags "database,connection"
```

### case list - 列出案例

#### 选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--limit` | `-l` | 返回数量 | `20` |

#### 示例

```bash
dte-diag case list --limit 20
```

---

## 集群管理命令 (cluster)

### cluster list - 列出可用集群

```bash
dte-diag cluster list
```

### cluster status - 查看集群状态

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `cluster_name` | 是 | 集群名称 |

#### 示例

```bash
dte-diag cluster status prod-01
```

### cluster test - 测试集群连接

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `cluster_name` | 是 | 集群名称 |

#### 选项

| 选项 | 简写 | 说明 |
|------|------|------|
| `--node` | `-n` | 测试指定节点 |

#### 示例

```bash
dte-diag cluster test prod-01

dte-diag cluster test prod-01 --node 192.168.1.100
```

---

## 配置管理命令 (config)

### config show - 查看当前配置

```bash
dte-diag config show
```

### config set - 设置配置项

#### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `key` | 是 | 配置项键名（支持点分隔的嵌套键） |
| `value` | 是 | 配置项值 |

#### 示例

```bash
dte-diag config set default.cluster prod-01
dte-diag config set api.timeout 600
```

### config init - 初始化配置文件

#### 选项

| 选项 | 简写 | 说明 |
|------|------|------|
| `--api-url` | `-u` | API服务地址 |
| `--api-key` | `-k` | API认证密钥 |

#### 示例

```bash
dte-diag config init --api-url http://localhost:8080
```

---

## 输出格式说明

CLI支持多种输出格式，通过 `--output` 或 `-o` 全局选项指定。

### table 格式（默认）

表格形式展示，适合人类阅读：

```
Session ID       Status      Cluster    Description          Created At
diag-20240115-001 completed   prod-01    数据库连接超时        2024-01-15 10:30
diag-20240115-002 running     prod-02    服务响应缓慢          2024-01-15 11:00
```

### json 格式

JSON格式输出，适合程序处理：

```json
{
  "session_id": "diag-20240115-001",
  "status": "completed",
  "cluster_name": "prod-01",
  "description": "数据库连接超时"
}
```

### yaml 格式

YAML格式输出：

```yaml
session_id: diag-20240115-001
status: completed
cluster_name: prod-01
description: 数据库连接超时
```

### text 格式

纯文本格式，适合脚本处理：

```
诊断会话: diag-20240115-001
状态: 已完成
集群: prod-01
问题描述: 数据库连接超时
创建时间: 2024-01-15 10:30:00

诊断结果:
问题类别: 数据库连接问题
置信度: 85%
最可能原因: 数据库连接池配置不足
建议操作:
  1. 检查连接池配置
  2. 分析连接持有时间
```

### markdown 格式

Markdown格式，适合文档输出：

```markdown
## 诊断报告 - diag-20240115-001

### 问题摘要
数据库连接超时

### 诊断结果
- **问题类别**: 数据库连接问题
- **置信度**: 85%
- **严重程度**: 高

### 可能原因
1. 数据库连接池配置不足 (85%)
2. 存在连接泄漏 (60%)

### 建议方案
1. 检查连接池配置
2. 分析连接持有时间
```

---

## 配置文件格式

配置文件位置：`~/.dte-diag/config.yaml`

### 完整配置示例

```yaml
api:
  url: http://localhost:8080
  key: your-api-key
  timeout: 300

defaults:
  cluster: prod-01
  service: DTEBaseService
  output: table
  priority: medium

auth:
  ssh_key_path: ~/.ssh/id_rsa
  username: admin

logging:
  level: info
  file: ~/.dte-diag/logs/dte-diag.log
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api.url` | API服务地址 | `http://localhost:8080` |
| `api.key` | API认证密钥 | - |
| `api.timeout` | API请求超时时间(秒) | `300` |
| `defaults.cluster` | 默认集群名称 | - |
| `defaults.service` | 默认服务名称 | `DTEBaseService` |
| `defaults.output` | 默认输出格式 | `table` |
| `defaults.priority` | 默认优先级 | `medium` |
| `auth.ssh_key_path` | SSH密钥路径 | - |
| `auth.username` | 默认登录用户名 | - |
| `logging.level` | 日志级别 | `info` |
| `logging.file` | 日志文件路径 | - |

---

## 使用技巧

### 1. 使用配置文件简化命令

设置默认集群和API地址后，无需每次指定：

```bash
dte-diag config init --api-url http://192.168.1.100:8080
dte-diag config set defaults.cluster prod-01
```

之后执行诊断时只需：

```bash
dte-diag diagnose -d "服务异常"
```

### 2. 使用环境变量传递API密钥

避免在命令行中暴露API密钥：

```bash
export DTE_DIAG_API_KEY=your-api-key
dte-diag cluster list
```

### 3. 结合 jq 处理JSON输出

```bash
dte-diag -o json history --limit 10 | jq '.items[] | .session_id'
```

### 4. 使用 --wait 和 --follow 跟踪诊断

```bash
dte-diag diagnose -d "问题" -C prod-01 --wait
dte-diag diagnose -d "问题" -C prod-01 --follow
```

### 5. 输出诊断报告到文件

```bash
dte-diag status diag-001 --format markdown > report.md
```

### 6. 批量诊断脚本

```bash
for cluster in prod-01 prod-02 prod-03; do
  dte-diag diagnose -d "健康检查" -C $cluster --wait
done
```

### 7. 使用 --dry-run 验证参数

```bash
dte-diag diagnose -d "测试问题" -C prod-01 --dry-run
```

### 8. 搜索历史案例辅助诊断

在执行诊断前，先搜索类似案例：

```bash
dte-diag search --query "连接超时" --category network
```

---

## 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 参数错误 |
| 3 | 认证失败 |
| 4 | 网络错误 |
| 5 | 服务器错误 |

---

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `DTE_DIAG_API_KEY` | API认证密钥 |
| `DTE_DIAG_API_URL` | API服务地址 |
| `DTE_DIAG_CONFIG` | 配置文件路径 |