"""Test database result format and extraction."""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dte_diagnostic_agent.tools.database import DatabaseQueryTool
from dte_diagnostic_agent.agent.info_extractor import ResultExtractor


async def test():
    print("Testing database_query tool return format...")
    result_str = await DatabaseQueryTool.coroutine(om_ip='localhost', db_name='rmtaskmgmtdb', sql='select * from table')
    print(f"Database result: {result_str}")
    
    result = json.loads(result_str)
    print(f"\nParsed result keys: {list(result.keys())}")
    print(f"Rows: {result.get('rows')}")
    
    print("\nTesting ResultExtractor with source='rows'...")
    extractor = ResultExtractor()
    extract_rules = {
        'last_error_code': {
            'method': 'field',
            'source': 'rows',
            'params': {'field_name': 'last_error_code'}
        }
    }
    
    extracted = extractor.extract(result, ['last_error_code'], extract_rules, 'test-session')
    print(f"Extracted: {extracted}")
    
    if extracted.get('last_error_code') == 'csm.loading.error':
        print("\n✓ Test passed: last_error_code correctly extracted from rows!")
    else:
        print(f"\n✗ Test failed: expected 'csm.loading.error', got {extracted.get('last_error_code')}")


if __name__ == "__main__":
    asyncio.run(test())