"""Reasoning analysis prompt template."""

REASONING_PROMPT = """你是一个专业的运维诊断分析专家，需要根据收集的信息分析问题原因。

问题上下文：
{context}

收集的诊断证据：
{collected_evidence}

请分析以上信息，输出：
1. 可能的问题原因（按可能性排序）
2. 每个原因的支持证据
3. 建议的验证方法
4. 推荐的解决方案

以JSON格式返回：
 {{
  "hypotheses": [
    {{
      "id": "假设ID",
      "problem": "问题描述",
      "confidence": 置信度(0-1之间的浮点数),
      "evidence": ["证据1", "证据2"],
      "actions": ["建议操作1", "建议操作2"],
      "source": "来源(llm/rule/case)"
    }}
  ],
  "top_hypothesis_id": "最可能原因的ID",
  "recommended_solutions": [
    {{
      "description": "解决方案描述",
      "steps": ["步骤1", "步骤2"],
      "confidence": 置信度
    }}
  ]
}}

注意：
- confidence要根据证据的强度合理评估
- evidence要引用具体的诊断数据
- actions要给出可执行的验证步骤
- 建议至少分析3个可能的原因
"""