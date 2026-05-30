"""Tool metadata registry for dynamic prompt generation."""

from dataclasses import dataclass
from typing import Any, List, Optional

from langchain_core.tools import StructuredTool


@dataclass
class ParameterInfo:
    """Parameter metadata."""
    name: str
    type: str
    description: str
    required: bool
    default: Any = None


@dataclass
class ToolMetadata:
    """Complete tool metadata including output examples."""
    name: str
    description: str
    parameters: List[ParameterInfo]
    output_example: Optional[str] = None


def extract_parameters_from_tool(tool: StructuredTool) -> List[ParameterInfo]:
    """Extract parameter information from tool's args_schema."""
    parameters = []
    
    if not tool.args_schema:
        return parameters
    
    schema = tool.args_schema.model_fields
    
    for field_name, field_info in schema.items():
        # 获取参数类型
        annotation = field_info.annotation
        if hasattr(annotation, '__name__'):
            param_type = annotation.__name__
        else:
            param_type = str(annotation).split('.')[-1].replace('typing.', '')
        
        # 判断是否必需：字段没有默认值时是必需的
        required = field_info.is_required()
        
        # 获取默认值
        default = None
        if field_info.default is not None and not str(field_info.default).startswith("Pydantic"):
            default = str(field_info.default)
        
        param = ParameterInfo(
            name=field_name,
            type=param_type,
            description=field_info.description or "",
            required=required,
            default=default
        )
        parameters.append(param)
    
    return parameters


def format_tool_metadata(tool: StructuredTool) -> ToolMetadata:
    """Format complete tool metadata."""
    parameters = extract_parameters_from_tool(tool)

    # 从 metadata 获取 output_example
    output_example = None
    if tool.metadata and isinstance(tool.metadata, dict):
        output_example = tool.metadata.get("output_example")

    return ToolMetadata(
        name=tool.name,
        description=tool.description,
        parameters=parameters,
        output_example=output_example
    )


def generate_tool_docs_string(tools: List[StructuredTool]) -> str:
    """Generate human-readable tool documentation string for prompt."""
    docs = []
    docs.append("## 可用工具列表\n")
    
    for idx, tool in enumerate(tools, start=1):
        metadata = format_tool_metadata(tool)
        
        docs.append(f"### {idx}. {metadata.name}")
        docs.append(metadata.description)
        
        # 参数说明
        docs.append("**参数**:")
        for param in metadata.parameters:
            req_str = "required" if param.required else "optional"
            default_str = f" (默认{param.default})" if param.default is not None else ""
            docs.append(f"- {param.name} ({param.type}, {req_str}): {param.description}{default_str}")
        
        # 输出结构说明
        if metadata.output_example:
            docs.append("\n**输出结构**:")
            docs.append(metadata.output_example)
        
        docs.append("")  # 空行分隔
    
    return "\n".join(docs)
