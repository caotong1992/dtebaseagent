"""Output formatting for dte-diag CLI tool."""

import json
from datetime import datetime
from enum import Enum
from typing import Any

import yaml


class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    MARKDOWN = "markdown"


class OutputFormatter:
    """Output formatter for dte-diag CLI results."""

    def __init__(self, format: OutputFormat = OutputFormat.TABLE, no_color: bool = False):
        self.format = format
        self.no_color = no_color

    def format_result(self, data: Any, headers: list[str] | None = None) -> str:
        match self.format:
            case OutputFormat.JSON:
                return self._format_json(data)
            case OutputFormat.YAML:
                return self._format_yaml(data)
            case OutputFormat.TEXT:
                return self._format_text(data)
            case OutputFormat.MARKDOWN:
                return self._format_markdown(data)
            case OutputFormat.TABLE:
                return self._format_table(data, headers)
            case _:
                return self._format_table(data, headers)

    def _format_json(self, data: Any) -> str:
        return json.dumps(self._serialize(data), indent=2, ensure_ascii=False)

    def _format_yaml(self, data: Any) -> str:
        return yaml.dump(self._serialize(data), default_flow_style=False, allow_unicode=True)

    def _format_text(self, data: Any) -> str:
        if isinstance(data, dict):
            return self._format_dict_text(data)
        elif isinstance(data, list):
            return self._format_list_text(data)
        return str(data)

    def _format_dict_text(self, data: dict[str, Any]) -> str:
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _format_list_text(self, data: list[Any]) -> str:
        if not data:
            return "无数据"
        if isinstance(data[0], dict):
            lines = []
            for i, item in enumerate(data, 1):
                lines.append(f"\n--- 记录 {i} ---")
                lines.append(self._format_dict_text(item))
            return "\n".join(lines)
        return "\n".join(str(item) for item in data)

    def _format_markdown(self, data: Any) -> str:
        if isinstance(data, dict):
            return self._format_dict_markdown(data)
        elif isinstance(data, list):
            return self._format_list_markdown(data)
        return str(data)

    def _format_dict_markdown(self, data: dict[str, Any]) -> str:
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"\n### {key}\n")
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
            elif isinstance(value, list):
                lines.append(f"\n### {key}\n")
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    def _format_list_markdown(self, data: list[Any]) -> str:
        if not data:
            return "无数据"
        if isinstance(data[0], dict):
            lines = ["| 字段 | 值 |", "|------|-----|"]
            for item in data[:20]:
                for key, value in item.items():
                    lines.append(f"| {key} | {value} |")
            return "\n".join(lines)
        items = "\n".join(f"- {item}" for item in data)
        return items

    def _format_table(self, data: Any, headers: list[str] | None = None) -> str:
        if not isinstance(data, list):
            return self._format_text(data)
        if not data:
            return "无数据"

        if headers is None:
            if isinstance(data[0], dict):
                headers = list(data[0].keys())
            else:
                headers = ["值"]

        col_widths = self._calculate_column_widths(data, headers)

        header_line = " | ".join(
            self._pad_cell(h, col_widths[i]) for i, h in enumerate(headers)
        )
        separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

        rows = []
        for item in data[:100]:
            if isinstance(item, dict):
                row = " | ".join(
                    self._pad_cell(str(item.get(h, "")), col_widths[i])
                    for i, h in enumerate(headers)
                )
            else:
                row = " | ".join(self._pad_cell(str(item), col_widths[0]))
            rows.append(row)

        return "\n".join([header_line, separator] + rows)

    def _calculate_column_widths(self, data: list[Any], headers: list[str]) -> list[int]:
        widths = [len(h) for h in headers]
        for item in data[:100]:
            if isinstance(item, dict):
                for i, h in enumerate(headers):
                    cell_width = len(str(item.get(h, "")))
                    widths[i] = max(widths[i], min(cell_width, 50))
        return widths

    def _pad_cell(self, text: str, width: int) -> str:
        truncated = text[:50] if len(text) > 50 else text
        return truncated.ljust(width)

    def _serialize(self, data: Any) -> Any:
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize(item) for item in data]
        elif hasattr(data, "model_dump"):
            return data.model_dump()
        return data

    def print(self, data: Any, headers: list[str] | None = None) -> None:
        result = self.format_result(data, headers)
        print(result)

    def print_error(self, message: str) -> None:
        if not self.no_color:
            print(f"\033[91m错误: {message}\033[0m")
        else:
            print(f"错误: {message}")

    def print_success(self, message: str) -> None:
        if not self.no_color:
            print(f"\033[92m{message}\033[0m")
        else:
            print(message)

    def print_info(self, message: str) -> None:
        if not self.no_color:
            print(f"\033[94m{message}\033[0m")
        else:
            print(message)

    def print_warning(self, message: str) -> None:
        if not self.no_color:
            print(f"\033[93m警告: {message}\033[0m")
        else:
            print(f"警告: {message}")