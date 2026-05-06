# DTE Diagnostic Agent

DTEBaseService 问题定位 AI Agent，用于智能诊断 DTEBaseService 服务问题，支持跨多个私有集群的运维场景。

## 技术栈

- Python 3.14
- LangChain 2.15.4
- OpenAI API
- FastAPI
- Click CLI

## 快速开始

### 环境准备

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置 LLM_API_KEY
```

### 启动服务

**Windows:**
```batch
bin\start.bat [port] [--restart|-r]
```

**Linux:**
```bash
./bin/start.sh [port] [--restart|-r]
```

| 参数 | 说明 |
|------|------|
| `port` | 服务端口，默认 8080 |
| `--restart` 或 `-r` | 强制重启，停止现有进程后重新启动 |

**示例:**
```batch
# Normal start (skip if same process running)
bin\start.bat

# Start on custom port
bin\start.bat 9090

# Force restart
bin\start.bat --restart
bin\start.bat -r

# Force restart on custom port
bin\start.bat 9090 --restart
```

**启动特性:**
- 检测 PID 文件，判断是否为同一进程
- 同一进程运行时跳过重启（节省资源）
- 不同进程占用端口时自动停止旧进程
- 启动后自动保存 PID 到 `bin/dte-diag.pid`

### 停止服务

**Windows:**
```batch
bin\stop.bat [port]
```

**Linux:**
```bash
./bin/stop.sh [port]
```

**示例:**
```batch
# Stop service on default port
bin\stop.bat

# Stop service on custom port
bin\stop.bat 9090
```

**停止特性:**
- 通过端口查找进程 PID
- 强制停止进程 (`taskkill /F` 或 `kill`)
- 自动清理 PID 文件

### 访问 API

- API 文档: http://localhost:8080/docs
- 健康检查: http://localhost:8080/api/v1/health

## 项目结构

```
dte_diagnostic_agent/
├── agent/          # Agent 核心模块
│   ├── core.py     # 诊断流程主类
│   ├── intent_parser.py  # 意图解析
│   ├── planner.py  # 诊断规划
│   ├── reasoning.py  # 推理分析
│   └── models/     # 数据模型
├── api/            # RESTful API 接口
│   ├── main.py     # FastAPI 应用
│   ├── routes/     # 路由模块
│   └── schemas/    # 数据模型
├── cli/            # 命令行工具
│   ├── main.py     # CLI 入口
│   └── commands/   # 命令实现
├── kb/             # 知识库管理
│   ├── manager.py  # 知识库管理器
│   ├── local_kb.py # 本地 Markdown 适配器
│   ├── remote_kb.py # 远程 API 适配器
│   ├── query_processor.py  # 查询预处理器
│   └── translator.py  # 翻译服务
├── prompts/        # Prompt 模板
├── storage/        # 数据存储
├── tools/          # 诊断工具集
└── __main__.py     # 启动入口
```

## CLI 命令

```bash
# 执行诊断
dte-diag diagnose "问题描述"

# 查询诊断状态
dte-diag status <session_id>

# 查看历史记录
dte-diag history

# 搜索案例库
dte-diag search "关键词"

# 案例管理
dte-diag case show <case_id>
dte-diag case list

# 集群管理
dte-diag cluster list
dte-diag cluster status <name>

# 配置管理
dte-diag config show
dte-diag config init
```

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/diagnose` | POST | 创建诊断任务 |
| `/api/v1/diagnose/{id}` | GET | 查询诊断状态 |
| `/api/v1/diagnose/list` | GET | 诊断任务列表 |
| `/api/v1/cases/search` | GET | 搜索案例库 |
| `/api/v1/cases/{id}` | GET | 获取案例详情 |
| `/api/v1/clusters` | GET | 集群列表 |
| `/api/v1/health` | GET | 健康检查 |

## 诊断流程

```
用户输入 → 意图解析 → 案例检索 → 规划生成 → 工具执行 → 推理分析 → 报告生成
```

1. **意图解析**: 提取问题描述、时间范围、环境信息
2. **案例检索**: 检索相似历史案例（支持中英文双语关键词检索）
3. **规划生成**: 生成诊断步骤
4. **工具执行**: SSH 连接、日志分析、资源检查等
5. **推理分析**: 规则推理 + LLM 推理
6. **报告生成**: 生成诊断报告和解决方案

## 配置文件

```yaml
# config.yaml
server:
  host: 0.0.0.0
  port: 8080

llm:
  api_key: ${LLM_API_KEY}
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model_name: glm-5

knowledge_base:
  mode: local
  query_processor:
    enabled: true
    use_llm_translation: true
```

## 知识库管理

知识库支持两种模式：

- **local**: 本地 Markdown 文件（默认）
- **remote**: 远程 API 服务

案例文件格式：

```markdown
---
case_id: CASE-001
title: 数据库连接超时
category: database
tags: [database, timeout]
---
## 问题现象
...

## 解决方案
...
```

## 日志

日志文件位于 `logs/agent.log`，按自然月存储诊断记录于 `data/sessions/sessions_YYYY-MM.csv`。

## 文档

- [API 文档](docs/api.md)
- [CLI 文档](docs/cli.md)
- [设计文档](design.md)
- [源码总结](AGENTS.md)

## 许可证

MIT License