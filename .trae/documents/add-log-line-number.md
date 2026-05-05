# 日志打印增加代码行号

## 问题分析

当前日志格式（`__main__.py` 第203-206行）：
```python
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

输出示例：
```
2026-05-04 20:39:01,976 - httpx - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
```

**缺少信息**：无法知道日志具体打印在哪个文件的哪一行。

## 修复方案

修改日志格式，添加 `%(filename)s` 和 `%(lineno)d` 字段：

**目标格式**：
```
%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s
```

**输出示例**：
```
2026-05-04 20:39:01,976 - httpx - INFO - [_client.py:102] - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 401 Unauthorized"
```

## 实施步骤

### 步骤1: 修改 `setup_logging` 函数

修改 `src/dte_diagnostic_agent/__main__.py` 第205行：

```python
# 原格式
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",

# 新格式
format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
```

### 步骤2: 可选增强 - 添加函数名

如果需要更详细的定位信息，可添加 `%(funcName)s`：

```python
format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d:%(funcName)s] - %(message)s"
```

输出：
```
2026-05-04 20:39:01,976 - httpx - INFO - [_client.py:102:send] - HTTP Request: POST...
```

## 涉及文件

| 文件 | 修改行 |
|------|--------|
| src/dte_diagnostic_agent/__main__.py | 第205行 format 字符串 |

## 可选：日志格式说明

| 字段 | 说明 | 示例 |
|------|------|------|
| %(asctime)s | 时间 | 2026-05-04 20:39:01,976 |
| %(name)s | logger名称 | httpx |
| %(levelname)s | 级别 | INFO |
| %(filename)s | 文件名 | _client.py |
| %(lineno)d | 行号 | 102 |
| %(funcName)s | 函数名 | send |
| %(message)s | 消息内容 | HTTP Request... |

## 测试验证

启动服务后检查日志输出格式是否包含代码行号：
```
2026-05-04 ... - [filename:line] - message
```