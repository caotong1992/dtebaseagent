"""Key information extractor for diagnostic results."""

import re
import logging
from typing import Any

from dte_diagnostic_agent.agent.models.context import DiagnosticContext

logger = logging.getLogger(__name__)


class KeyInfoExtractor:
    """从工具执行结果中提取关键信息"""

    ERROR_CODE_PATTERN = r'(csm\.[a-z]+\.[a-z]+|data\.[a-z]+\.[a-z]+|send\.[a-z]+\.[a-z]+|task\.[a-z]+\.[a-z]+)'

    def extract_last_error_code(self, result: dict[str, Any], session_id: str = "") -> str | None:
        """从数据库查询结果提取 last_error_code

        Args:
            result: 工具执行结果字典，可能包含 rows 或 raw_result
            session_id: 会话ID，用于日志追踪

        Returns:
            提取到的错误码，未找到返回 None
        """
        if "rows" in result:
            rows = result["rows"]
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict) and "last_error_code" in row:
                        error_code = row["last_error_code"]
                        if error_code:
                            logger.info(f"[{session_id}] [KeyInfoExtractor] 从 rows 中提取到 last_error_code: {error_code}")
                            return str(error_code)

        raw = result.get("raw_result", "")
        if isinstance(raw, str) and raw:
            match = re.search(self.ERROR_CODE_PATTERN, raw)
            if match:
                error_code = match.group(1)
                logger.info(f"[{session_id}] [KeyInfoExtractor] 从 raw_result 中匹配到错误码: {error_code}")
                return error_code

        logger.info(f"[{session_id}] [KeyInfoExtractor] 未找到 last_error_code")
        return None

    def extract_task_id(self, context: DiagnosticContext, session_id: str = "") -> str | None:
        """从上下文提取 task_id

        Args:
            context: 诊断上下文
            session_id: 会话ID，用于日志追踪

        Returns:
            提取到的 task_id，未找到返回 None
        """
        desc = context.problem_description
        match = re.search(r'task[_-]?id[:\s=]+(\w+)', desc, re.IGNORECASE)
        if match:
            task_id = match.group(1)
            logger.info(f"[{session_id}] [KeyInfoExtractor] 从 problem_description 提取到 task_id: {task_id}")
            return task_id

        for symptom in context.symptoms:
            match = re.search(r'task[_-]?id[:\s=]+(\w+)', symptom, re.IGNORECASE)
            if match:
                task_id = match.group(1)
                logger.info(f"[{session_id}] [KeyInfoExtractor] 从 symptoms 提取到 task_id: {task_id}")
                return task_id

        logger.info(f"[{session_id}] [KeyInfoExtractor] 未找到 task_id")
        return None


class ResultExtractor:
    """通用结果提取器"""

    def extract(
        self,
        result: dict[str, Any],
        output_vars: list[str],
        extract_rules: dict[str, Any],
        session_id: str = ""
    ) -> dict[str, str | None]:
        """根据提取规则从结果中提取变量值

        Args:
            result: 工具执行结果字典
            output_vars: 需要提取的变量名列表
            extract_rules: 提取规则字典，key为变量名，value为提取规则
            session_id: 会话ID，用于日志追踪

        Returns:
            提取结果字典，key为变量名，value为提取到的值或None
        """
        extracted: dict[str, str | None] = {}
        for var_name in output_vars:
            rule = extract_rules.get(var_name, {})
            if not rule:
                logger.info(f"[{session_id}] [ResultExtractor] 变量 {var_name} 无提取规则，跳过")
                extracted[var_name] = None
                continue

            method = rule.get("method", "")
            source = rule.get("source", "")
            params = rule.get("params", {})

            source_data = result.get(source)
            if source_data is None:
                logger.info(f"[{session_id}] [ResultExtractor] 变量 {var_name} 的源数据 {source} 不存在")
                extracted[var_name] = None
                continue

            value = None
            if method == "field":
                field_name = params.get("field_name", "")
                value = self._extract_by_field(source_data, field_name, session_id)
            elif method == "regex":
                pattern = params.get("pattern", "")
                value = self._extract_by_regex(str(source_data), pattern, session_id)
            elif method == "json_path":
                path = params.get("path", "")
                value = self._extract_by_json_path(source_data, path, session_id)
            else:
                logger.info(f"[{session_id}] [ResultExtractor] 变量 {var_name} 的提取方法 {method} 不支持")

            extracted[var_name] = value
            if value is not None:
                logger.info(f"[{session_id}] [ResultExtractor] 变量 {var_name} 提取成功: {value}")

        return extracted

    def _extract_by_field(self, source_data: Any, field_name: str, session_id: str = "") -> str | None:
        """从源数据中按字段名提取值

        Args:
            source_data: 源数据，通常是 list[dict] 或 dict
            field_name: 要提取的字段名
            session_id: 会话ID，用于日志追踪

        Returns:
            提取到的字段值，未找到返回 None
        """
        if not field_name:
            logger.info(f"[{session_id}] [ResultExtractor] _extract_by_field: field_name 为空")
            return None

        if isinstance(source_data, list):
            for item in source_data:
                if isinstance(item, dict) and field_name in item:
                    value = item[field_name]
                    if value is not None:
                        logger.info(f"[{session_id}] [ResultExtractor] _extract_by_field: 从 list 中提取字段 {field_name} 成功")
                        return str(value)
        elif isinstance(source_data, dict):
            if field_name in source_data:
                value = source_data[field_name]
                if value is not None:
                    logger.info(f"[{session_id}] [ResultExtractor] _extract_by_field: 从 dict 中提取字段 {field_name} 成功")
                    return str(value)

        logger.info(f"[{session_id}] [ResultExtractor] _extract_by_field: 未找到字段 {field_name}")
        return None

    def _extract_by_regex(self, source_data: str, pattern: str, session_id: str = "") -> str | None:
        """使用正则表达式从字符串中提取值

        Args:
            source_data: 源字符串
            pattern: 正则表达式模式
            session_id: 会话ID，用于日志追踪

        Returns:
            提取到的第一个匹配结果，未匹配返回 None
        """
        if not source_data or not pattern:
            logger.info(f"[{session_id}] [ResultExtractor] _extract_by_regex: source_data 或 pattern 为空")
            return None

        try:
            match = re.search(pattern, source_data)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                logger.info(f"[{session_id}] [ResultExtractor] _extract_by_regex: 匹配成功")
                return value
        except re.error as e:
            logger.warning(f"[{session_id}] [ResultExtractor] _extract_by_regex: 正则表达式错误: {e}")
            return None

        logger.info(f"[{session_id}] [ResultExtractor] _extract_by_regex: 未匹配到结果")
        return None

    def _extract_by_json_path(self, source_data: Any, path: str, session_id: str = "") -> str | None:
        """使用 JSON 路径表达式从数据中提取值

        支持简单的点分隔路径和数组索引，如 "rows[0].last_error_code"

        Args:
            source_data: 源数据（dict 或 list）
            path: JSON 路径表达式
            session_id: 会话ID，用于日志追踪

        Returns:
            提取到的值，未找到返回 None
        """
        if not path:
            logger.info(f"[{session_id}] [ResultExtractor] _extract_by_json_path: path 为空")
            return None

        current = source_data
        parts = path.split(".")
        array_index_pattern = re.compile(r"^(.+?)\[(\d+)\]$")

        try:
            for part in parts:
                if current is None:
                    break

                match = array_index_pattern.match(part)
                if match:
                    key = match.group(1)
                    index = int(match.group(2))
                    if isinstance(current, dict) and key in current:
                        arr = current[key]
                        if isinstance(arr, list) and 0 <= index < len(arr):
                            current = arr[index]
                        else:
                            current = None
                            break
                    else:
                        current = None
                        break
                else:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break

            if current is not None:
                logger.info(f"[{session_id}] [ResultExtractor] _extract_by_json_path: 路径 {path} 提取成功")
                return str(current)
        except (KeyError, IndexError, TypeError) as e:
            logger.info(f"[{session_id}] [ResultExtractor] _extract_by_json_path: 提取失败: {e}")

        logger.info(f"[{session_id}] [ResultExtractor] _extract_by_json_path: 路径 {path} 未找到")
        return None