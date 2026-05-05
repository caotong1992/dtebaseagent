# 使用.env文件加载环境变量

## 问题分析

### 当前状态
- config.yaml 使用 `${LLM_API_KEY}` 格式的环境变量占位符
- load_config 函数直接使用 yaml.safe_load，不支持环境变量替换
- 缺少 .env 文件支持

### 目标
实现从 .env 文件加载环境变量，并支持在 config.yaml 中使用 `${VAR_NAME}` 格式引用环境变量。

## 修复方案

### 步骤1: 添加依赖
在 requirements.txt 中添加 `python-dotenv` 依赖。

**修改文件**: requirements.txt
```python
# Environment Variables
python-dotenv>=1.0.0
```

### 步骤2: 创建 .env.example 示例文件
创建 .env.example 作为环境变量配置模板。

**新建文件**: .env.example
```env
# LLM Configuration
LLM_API_KEY=your-api-key-here

# Authentication
DTE_DIAG_API_KEY=your-api-key-here
```

### 步骤3: 修改 __main__.py
在配置加载前添加环境变量支持：

**修改文件**: __main__.py

1. 导入 dotenv：
```python
from dotenv import load_dotenv
```

2. 在 load_config 函数开头加载 .env：
```python
def load_config(config_path: Path | None = None) -> AppConfig:
    # 加载 .env 文件（优先级：当前目录 > 项目根目录）
    load_dotenv()
    load_dotenv(Path(".env"))
    ...
```

3. 添加环境变量替换函数：
```python
def _expand_env_vars(data: Any) -> Any:
    """递归替换配置中的环境变量占位符 ${VAR_NAME}"""
    if isinstance(data, str):
        # 匹配 ${VAR_NAME} 格式
        pattern = r'\$\{([^}]+)\}'
        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        return re.sub(pattern, replace, data)
    elif isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    return data
```

4. 在 yaml.safe_load 后调用替换函数：
```python
if found_path:
    with open(found_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data = _expand_env_vars(data)  # 替换环境变量
    config = AppConfig(**data)
```

### 步骤4: 更新 config.yaml 文档说明
修改 config.yaml 中 api_key 的注释说明：
```yaml
llm:
  # API密钥，可使用环境变量 ${LLM_API_KEY} 或直接填写
  api_key: ${LLM_API_KEY}
```

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| requirements.txt | 修改 | 添加 python-dotenv>=1.0.0 |
| .env.example | 新建 | 环境变量模板文件 |
| __main__.py | 修改 | 加载.env、添加环境变量替换 |
| config.yaml | 修改 | 添加注释说明 |

## 使用方式

1. 复制 .env.example 为 .env
2. 在 .env 中填写实际的环境变量值：
   ```env
   LLM_API_KEY=sk-xxxxx
   ```
3. config.yaml 保持 `${LLM_API_KEY}` 占位符
4. 启动服务时自动加载 .env 并替换配置中的环境变量