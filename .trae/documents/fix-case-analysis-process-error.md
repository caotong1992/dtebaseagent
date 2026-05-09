# 分析 'Case' object has no attribute 'analysis_process' 错误

## 问题现象

日志显示错误：
```
阶段: diagnose, 错误: 'Case' object has no attribute 'analysis_process'
```

## 根本原因

**属性名称引用错误**：

| 文件 | 问题代码 | 错误 |
|------|---------|------|
| [planner.py:105](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/agent/planner.py#L105) | `case.analysis_process` | 引用了不存在的属性 |

**Case 模型定义** ([models.py:16](file:///d:/code/dtebaseagent/src/dte_diagnostic_agent/kb/models.py#L16))：

```python
analysis: str = Field(default="", description="Analysis process")
```

属性名是 `analysis`，不是 `analysis_process`。

## 实施步骤

### Step 1: 修复 planner.py 属性引用

修改 `src/dte_diagnostic_agent/agent/planner.py` 第 105 行：

```python
# 错误
lines.append(f"   分析过程: {case.analysis_process}")

# 正确
lines.append(f"   分析过程: {case.analysis}")
```

## 验证清单

- [x] planner.py 中 `analysis_process` 改为 `analysis`
- [x] 重启服务后诊断任务执行成功