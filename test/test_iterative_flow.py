"""Test case_search iterative flow."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dte_diagnostic_agent.kb.manager import KnowledgeBaseManager
from dte_diagnostic_agent.kb.config import KnowledgeBaseConfig, LocalKBConfig
from dte_diagnostic_agent.agent.core import DTEBaseDiagnosticAgent
from dte_diagnostic_agent.agent.models.input import UserInput


async def test_iterative_flow():
    kb_config = KnowledgeBaseConfig(
        mode="local",
        local=LocalKBConfig(
            case_dir=os.path.join(os.path.dirname(__file__), '..', 'cases'),
            file_pattern="**/*.md"
        )
    )
    kb_manager = KnowledgeBaseManager(kb_config)
    
    agent = DTEBaseDiagnosticAgent(
        api_key=os.environ.get("OPENAI_API_KEY", "test-key"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
        model_name="gpt-4o",
        temperature=0.1,
        kb_manager=kb_manager
    )
    
    user_input = UserInput(
        description="采集任务失败，taskId: 123456",
        environment={"cluster_name": "prod-01"}
    )
    
    print("Starting diagnostic test...")
    report = await agent.diagnose(user_input, session_id="test-session-001")
    
    print("\n=== Diagnostic Report ===")
    print(f"Session ID: {report.session_id}")
    print(f"Summary: {report.summary}")
    print(f"Collected Data Keys: {list(report.collected_evidence.keys())}")
    
    if report.similar_cases:
        print(f"Similar Cases: {[c.case_id for c in report.similar_cases]}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(test_iterative_flow())