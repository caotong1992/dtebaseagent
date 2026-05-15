"""Test dynamic result extraction."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dte_diagnostic_agent.agent.models.parsed_step import ExtractRule, ExtractType, ParsedStep
from dte_diagnostic_agent.agent.info_extractor import KeyInfoExtractor, ResultExtractor

print("Testing ExtractRule model...")
er = ExtractRule(source="rows", type=ExtractType.FIELD, value="last_error_code")
print(f"ExtractRule: source={er.source}, type={er.type}, value={er.value}")

print("\nTesting ParsedStep with output_vars and extract_rules...")
ps = ParsedStep(
    step_number=1,
    action_type="tool_execute",
    tool_name="database_query",
    parameters={"sql": "select * from table"},
    description="query database",
    output_vars=["last_error_code"],
    extract_rules={"last_error_code": ExtractRule(source="rows", type=ExtractType.FIELD, value="last_error_code")}
)
print(f"ParsedStep.output_vars: {ps.output_vars}")
print(f"ParsedStep.extract_rules: {ps.extract_rules}")

print("\nTesting ResultExtractor...")
extractor = ResultExtractor()
test_result = {
    "rows": [{"last_error_code": "csm.loading.error", "task_id": "123456"}],
    "executed": True
}
extract_rules_dict = {
    "last_error_code": {
        "source": "rows",
        "type": "field",
        "value": "last_error_code"
    }
}
extracted = extractor.extract(test_result, ["last_error_code"], extract_rules_dict, "test-session")
print(f"Extracted: {extracted}")

print("\nAll tests passed!")