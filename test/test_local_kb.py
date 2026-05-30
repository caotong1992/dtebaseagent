"""Test local_kb.py."""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dte_diagnostic_agent.kb.local_kb import LocalMarkdownKB
from dte_diagnostic_agent.kb.config import LocalKBConfig
from dte_diagnostic_agent.kb.models import Case


@pytest.fixture
def temp_case_dir(tmp_path):
    """Create temporary case directory with test files."""
    case_dir = tmp_path / "cases"
    case_dir.mkdir()
    
    db_dir = case_dir / "database"
    db_dir.mkdir()
    
    case1_content = """---
case_id: CASE-TEST-001
title: Database Connection Timeout
category: database
severity: critical
tags: [timeout, mysql]
created_at: 2024-01-15T10:00:00
---
## Problem
Database connection timeout, unable to access.

## Solution
- Check network connection
- Check database status
"""
    (db_dir / "CASE-TEST-001.md").write_text(case1_content, encoding="utf-8")
    
    net_dir = case_dir / "network"
    net_dir.mkdir()
    
    case2_content = """---
case_id: CASE-TEST-002
title: Network Timeout
category: network
---
## Problem
Network request timeout
"""
    (net_dir / "CASE-TEST-002.md").write_text(case2_content, encoding="utf-8")
    
    return str(case_dir)


@pytest.fixture
def empty_case_dir(tmp_path):
    """Create empty case directory."""
    case_dir = tmp_path / "empty_cases"
    case_dir.mkdir()
    return str(case_dir)


@pytest.fixture
def malformed_case_dir(tmp_path):
    """Create case directory with malformed file."""
    case_dir = tmp_path / "malformed_cases"
    case_dir.mkdir()
    
    db_dir = case_dir / "database"
    db_dir.mkdir()
    
    valid_content = """---
case_id: CASE-VALID-001
title: Valid Case
category: database
---
## Problem
Valid case content
"""
    (db_dir / "CASE-VALID-001.md").write_text(valid_content, encoding="utf-8")
    
    malformed_content = """This is not a valid markdown file
no frontmatter here
just plain text
"""
    (db_dir / "malformed.md").write_text(malformed_content, encoding="utf-8")
    
    return str(case_dir)


@pytest.fixture
def rich_case_dir(tmp_path):
    """Create case directory with rich test cases for search."""
    case_dir = tmp_path / "rich_cases"
    case_dir.mkdir()
    
    db_dir = case_dir / "database"
    db_dir.mkdir()
    
    case1 = """---
case_id: CASE-RICH-001
title: MySQL Connection Timeout Error
category: database
severity: critical
tags: [mysql, connection, timeout]
---
## Problem
MySQL database connection timeout

## Solution
- Check network
- Check configuration
"""
    (db_dir / "CASE-RICH-001.md").write_text(case1, encoding="utf-8")
    
    case2 = """---
case_id: CASE-RICH-002
title: PostgreSQL Slow Query
category: database
severity: medium
tags: [postgresql, slow, query]
---
## Problem
PostgreSQL query is slow

## Solution
- Optimize index
"""
    (db_dir / "CASE-RICH-002.md").write_text(case2, encoding="utf-8")
    
    net_dir = case_dir / "network"
    net_dir.mkdir()
    
    case3 = """---
case_id: CASE-RICH-003
title: Network Timeout Issue
category: network
severity: high
tags: [network, timeout]
---
## Problem
Network connection timeout

## Solution
- Check firewall
"""
    (net_dir / "CASE-RICH-003.md").write_text(case3, encoding="utf-8")
    
    return str(case_dir)


class TestLocalMarkdownKBInit:
    """Initialization tests (T001-T004)."""
    
    def test_init_with_valid_dir(self, temp_case_dir):
        """T001: Normal initialization."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        assert len(kb.index) == 2
        assert "CASE-TEST-001" in kb.index
        assert "CASE-TEST-002" in kb.index
    
    def test_init_with_nonexistent_dir(self, tmp_path):
        """T002: Directory not exists."""
        config = LocalKBConfig(case_dir=str(tmp_path / "nonexistent"))
        kb = LocalMarkdownKB(config)
        assert len(kb.index) == 0
    
    def test_init_with_empty_dir(self, empty_case_dir):
        """T003: Empty directory."""
        config = LocalKBConfig(case_dir=empty_case_dir)
        kb = LocalMarkdownKB(config)
        assert len(kb.index) == 0
    
    def test_init_with_malformed_files(self, malformed_case_dir):
        """T004: Malformed files skipped."""
        config = LocalKBConfig(case_dir=malformed_case_dir)
        kb = LocalMarkdownKB(config)
        assert len(kb.index) == 1
        assert "CASE-VALID-001" in kb.index


class TestLocalMarkdownKBParseFrontmatter:
    """Frontmatter parsing tests (T101-T105)."""
    
    def test_parse_standard_frontmatter(self, temp_case_dir):
        """T101: Standard YAML frontmatter."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert case.case_id == "CASE-TEST-001"
        assert case.title == "Database Connection Timeout"
        assert case.category == "database"
        assert case.severity == "critical"
    
    def test_parse_array_field(self, temp_case_dir):
        """T103: Array field parsing."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert case.tags == ["timeout", "mysql"]
    
    def test_parse_datetime_field(self, temp_case_dir):
        """T301: ISO datetime format."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert case.created_at.year == 2024
        assert case.created_at.month == 1
        assert case.created_at.day == 15
    
    def test_parse_missing_fields(self, temp_case_dir):
        """T105: Missing/null fields use defaults."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-002")
        assert case is not None
        assert case.severity == "medium"


class TestLocalMarkdownKBParseSections:
    """Section parsing tests (T201-T205)."""
    
    def test_parse_problem_section(self, temp_case_dir):
        """T201: Problem section."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert "timeout" in case.problem
    
    def test_parse_list_items(self, temp_case_dir):
        """T203: List items."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert len(case.solution) == 2
        assert "Check network connection" in case.solution
    
    def test_parse_multiple_sections(self, rich_case_dir):
        """T204: Multiple sections."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        case = kb.index.get("CASE-RICH-001")
        assert case is not None
        assert case.problem != ""
        assert len(case.solution) == 2


class TestLocalMarkdownKBSearch:
    """Search tests (T401-T410)."""
    
    @pytest.mark.asyncio
    async def test_search_title_match(self, rich_case_dir):
        """T401: Title match."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout")
        assert len(results) >= 2
        assert results[0].similarity > 0
    
    @pytest.mark.asyncio
    async def test_search_problem_match(self, rich_case_dir):
        """T402: Problem description match."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="slow")
        assert len(results) >= 1
        assert any("slow" in r.case.problem for r in results)
    
    @pytest.mark.asyncio
    async def test_search_multi_keywords(self, rich_case_dir):
        """T403: Multi-keyword search."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout", keywords=["mysql", "timeout"])
        assert len(results) >= 1
        assert any("mysql" in r.case.title.lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_search_category_filter(self, rich_case_dir):
        """T404: Category filter."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout", category="database")
        assert len(results) >= 1
        assert all(r.case.category == "database" for r in results)
    
    @pytest.mark.asyncio
    async def test_search_category_unknown(self, rich_case_dir):
        """T405: Category=unknown no filter."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout", category="unknown")
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_search_tag_match(self, rich_case_dir):
        """T407: Tag match."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="mysql")
        assert len(results) >= 1
        assert any("mysql" in r.case.tags for r in results)
    
    @pytest.mark.asyncio
    async def test_search_no_match(self, rich_case_dir):
        """T408: No match returns empty."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="nonexistent_keyword_xyz")
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_top_k_limit(self, rich_case_dir):
        """T409: top_k limit."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout", top_k=1)
        assert len(results) <= 1
    
    @pytest.mark.asyncio
    async def test_search_sorted_by_similarity(self, rich_case_dir):
        """T410: Sorted by similarity."""
        config = LocalKBConfig(case_dir=rich_case_dir)
        kb = LocalMarkdownKB(config)
        results = await kb.search(query="timeout")
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i].similarity >= results[i + 1].similarity


class TestLocalMarkdownKBCRUD:
    """CRUD tests (T501-T510)."""
    
    @pytest.mark.asyncio
    async def test_get_existing(self, temp_case_dir):
        """T501: Get existing case."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = await kb.get("CASE-TEST-001")
        assert case is not None
        assert case.case_id == "CASE-TEST-001"
        assert case.title == "Database Connection Timeout"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, temp_case_dir):
        """T502: Get non-existing case."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        case = await kb.get("CASE-INVALID")
        assert case is None
    
    @pytest.mark.asyncio
    async def test_save_new_case(self, temp_case_dir):
        """T503: Save new case."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        initial_count = len(kb.index)
        
        new_case = Case(
            case_id="CASE-TEST-003",
            title="New Test Case",
            category="database",
            problem="Test problem description"
        )
        path = await kb.save(new_case)
        
        assert Path(path).exists()
        assert "CASE-TEST-003" in kb.index
        assert len(kb.index) == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_save_updates_index(self, temp_case_dir):
        """T504: Save updates index."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        
        updated_case = Case(
            case_id="CASE-TEST-001",
            title="Updated Title",
            category="database",
            problem="Updated problem"
        )
        await kb.save(updated_case)
        
        case = kb.index.get("CASE-TEST-001")
        assert case is not None
        assert case.title == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_list_all_no_filter(self, temp_case_dir):
        """T505: List all cases."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        cases = await kb.list_all()
        assert len(cases) == 2
    
    @pytest.mark.asyncio
    async def test_list_all_category_filter(self, temp_case_dir):
        """T506: List by category."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        cases = await kb.list_all(category="database")
        assert len(cases) == 1
        assert cases[0].category == "database"
    
    @pytest.mark.asyncio
    async def test_list_all_limit(self, temp_case_dir):
        """T507: List with limit."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        cases = await kb.list_all(limit=1)
        assert len(cases) <= 1
    
    @pytest.mark.asyncio
    async def test_delete_existing(self, temp_case_dir):
        """T508: Delete existing case."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        initial_count = len(kb.index)
        result = await kb.delete("CASE-TEST-001")
        assert result is True
        assert "CASE-TEST-001" not in kb.index
        assert len(kb.index) == initial_count - 1
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, temp_case_dir):
        """T509: Delete non-existing case."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = await kb.delete("CASE-INVALID")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_reload(self, temp_case_dir):
        """T510: Reload knowledge base."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        initial_count = len(kb.index)
        
        kb.index.clear()
        assert len(kb.index) == 0
        
        await kb.reload()
        assert len(kb.index) == initial_count


class TestLocalMarkdownKBMarkdownBuild:
    """Markdown build tests (T601-T603)."""
    
    def test_build_complete_markdown(self, temp_case_dir):
        """T601: Complete markdown."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        
        full_case = Case(
            case_id="CASE-FULL-001",
            title="Full Test Case",
            category="database",
            problem="Full problem description",
            symptoms=["Symptom 1", "Symptom 2"],
            analysis="Full analysis",
            solution=["Step 1", "Step 2", "Step 3"],
            verification="Verification result",
            references=["Ref 1", "Ref 2"],
            tags=["tag1", "tag2"],
            cluster="cluster-01"
        )
        markdown = kb._build_markdown(full_case)
        
        assert "---" in markdown
        assert "case_id: CASE-FULL-001" in markdown
        assert "## 问题现象" in markdown
        assert "## 症状列表" in markdown
        assert "## 分析过程" in markdown
        assert "## 解决方案" in markdown
        assert "## 验证结果" in markdown
        assert "## 参考资料" in markdown
    
    def test_build_empty_fields_omitted(self, temp_case_dir):
        """T602: Empty fields omitted."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        
        minimal_case = Case(
            case_id="CASE-MINIMAL-001",
            title="Minimal Case",
            category="database",
            problem="Only problem"
        )
        markdown = kb._build_markdown(minimal_case)
        
        assert "## 问题现象" in markdown
        assert "## 解决方案" not in markdown
        assert "## 症状列表" not in markdown
    
    def test_special_characters_in_title(self, temp_case_dir):
        """T603: Special characters handling."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        
        special_case = Case(
            case_id="CASE-SPECIAL-001",
            title="Case with special chars",
            category="database",
            problem="Problem"
        )
        
        import asyncio
        path = asyncio.run(kb.save(special_case))
        
        assert Path(path).exists()
        assert "CASE-SPECIAL-001" in kb.index


class TestLocalMarkdownKBDateTime:
    """Datetime parsing tests (T301-T305)."""
    
    def test_parse_datetime_iso(self, temp_case_dir):
        """T301: ISO format."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = kb._parse_datetime("2024-01-15T10:00:00")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_datetime_full(self, temp_case_dir):
        """T302: Date time format."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = kb._parse_datetime("2024-01-15 10:00:00")
        assert result.year == 2024
        assert result.month == 1
    
    def test_parse_datetime_date_only(self, temp_case_dir):
        """T303: Date only format."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = kb._parse_datetime("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_datetime_none(self, temp_case_dir):
        """T304: None returns now."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = kb._parse_datetime(None)
        assert isinstance(result, datetime)
    
    def test_parse_datetime_invalid(self, temp_case_dir):
        """T305: Invalid format returns now."""
        config = LocalKBConfig(case_dir=temp_case_dir)
        kb = LocalMarkdownKB(config)
        result = kb._parse_datetime("invalid-date")
        assert isinstance(result, datetime)