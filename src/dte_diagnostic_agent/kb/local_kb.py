"""Local markdown knowledge base implementation."""

import os
import re
from pathlib import Path
from datetime import datetime

from dte_diagnostic_agent.kb.interface import KnowledgeBaseInterface
from dte_diagnostic_agent.kb.models import Case, SearchResult
from dte_diagnostic_agent.kb.config import LocalKBConfig


class LocalMarkdownKB(KnowledgeBaseInterface):
    """Local markdown file knowledge base."""
    
    def __init__(self, config: LocalKBConfig):
        self.case_dir = Path(config.case_dir)
        self.index: dict[str, Case] = {}
        self._load_index()
    
    def _load_index(self) -> None:
        """Load all case files from directory."""
        if not self.case_dir.exists():
            return
        
        for md_file in self.case_dir.glob("**/*.md"):
            try:
                case = self._parse_case_file(md_file)
                if case and case.case_id:
                    self.index[case.case_id] = case
            except Exception as e:
                print(f"Warning: Failed to parse {md_file}: {e}")
    
    def _parse_case_file(self, file_path: Path) -> Case | None:
        """Parse markdown case file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            frontmatter, body = self._parse_frontmatter(content)
            sections = self._parse_sections(body)
            
            return Case(
                case_id=frontmatter.get("case_id", ""),
                title=frontmatter.get("title", ""),
                category=frontmatter.get("category", "unknown"),
                severity=frontmatter.get("severity", "medium"),
                symptoms=sections.get("symptoms", frontmatter.get("symptoms", [])),
                problem=sections.get("problem", frontmatter.get("problem", "")),
                analysis=sections.get("analysis", ""),
                solution=sections.get("solution", []),
                verification=sections.get("verification", ""),
                references=sections.get("references", []),
                related_cases=frontmatter.get("related_cases", []),
                created_at=self._parse_datetime(frontmatter.get("created_at")),
                updated_at=self._parse_datetime(frontmatter.get("updated_at")),
                tags=frontmatter.get("tags", []),
                cluster=frontmatter.get("cluster"),
                service=frontmatter.get("service"),
            )
        except Exception:
            return None
    
    def _parse_frontmatter(self, content: str) -> tuple[dict[str, object], str]:
        """Parse YAML frontmatter from markdown."""
        frontmatter = {}
        body = content
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                body = parts[2].strip()
                
                for line in yaml_content.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if value.startswith("[") and value.endswith("]"):
                            items = [item.strip().strip("'\"") for item in value[1:-1].split(",")]
                            frontmatter[key] = items
                        elif value in ["null", "None", ""]:
                            frontmatter[key] = None
                        else:
                            frontmatter[key] = value.strip("'\"")
        
        return frontmatter, body
    
    def _parse_sections(self, content: str) -> dict[str, object]:
        """Parse markdown sections."""
        sections = {}
        
        pattern = r"##\s+([\w\u4e00-\u9fa5]+)\s*\n(.*?)(?=##\s|$)"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for title, body in matches:
            title = title.strip()
            body = body.strip()
            
            section_key = self._translate_section(title)
            
            if title in ["症状列表", "解决方案", "参考资料", "Symptoms", "Solution", "References"]:
                items = []
                for line in body.split("\n"):
                    line = line.strip()
                    if line.startswith("- ") or line.startswith("* "):
                        items.append(line[2:].strip())
                    elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
                        items.append(line[3:].strip())
                sections[section_key] = items
            else:
                sections[section_key] = body
        
        return sections
    
    def _translate_section(self, title: str) -> str:
        """Translate section title to key."""
        mapping = {
            "问题现象": "problem",
            "症状列表": "symptoms",
            "问题原因": "problem",
            "分析过程": "analysis",
            "解决方案": "solution",
            "验证结果": "verification",
            "参考资料": "references",
            "Problem": "problem",
            "Symptoms": "symptoms",
            "Analysis": "analysis",
            "Solution": "solution",
            "Verification": "verification",
            "References": "references",
        }
        return mapping.get(title, title.lower())
    
    def _parse_datetime(self, value: str | None) -> datetime:
        """Parse datetime string."""
        if not value:
            return datetime.now()
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        return datetime.now()
    
    async def search(
        self,
        query: str,
        symptoms: list[str] | None = None,
        category: str | None = None,
        top_k: int = 10
    ) -> list[SearchResult]:
        """Keyword search for cases."""
        results = []
        query_lower = query.lower()
        
        for case in self.index.values():
            if category and case.category != category:
                continue
            
            score = 0
            match_reasons = []
            
            if query_lower in case.title.lower():
                score += 10
                match_reasons.append("标题匹配")
            
            if query_lower in case.problem.lower():
                score += 5
                match_reasons.append("问题描述匹配")
            
            for symptom in (symptoms or []):
                if symptom.lower() in [s.lower() for s in case.symptoms]:
                    score += 3
                    match_reasons.append(f"症状匹配: {symptom}")
            
            for tag in case.tags:
                if query_lower in tag.lower():
                    score += 2
                    match_reasons.append(f"标签匹配: {tag}")
            
            if score > 0:
                results.append(SearchResult(
                    case=case,
                    similarity=min(score / 20, 1.0),
                    match_reason="; ".join(match_reasons)
                ))
        
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:top_k]
    
    async def get(self, case_id: str) -> Case | None:
        """Get case by ID."""
        return self.index.get(case_id)
    
    async def save(self, case: Case) -> str:
        """Save case to markdown file."""
        case_dir = self.case_dir / case.category
        case_dir.mkdir(parents=True, exist_ok=True)
        
        title_slug = re.sub(r"[^\w\u4e00-\u9fa5a-z0-9]", "-", case.title.lower())
        title_slug = re.sub(r"-+", "-", title_slug).strip("-")
        file_name = f"{case.case_id}-{title_slug}.md"
        file_path = case_dir / file_name
        
        content = self._build_markdown(case)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.index[case.case_id] = case
        return str(file_path)
    
    def _build_markdown(self, case: Case) -> str:
        """Build markdown content from case."""
        lines = ["---"]
        lines.append(f"case_id: {case.case_id}")
        lines.append(f"title: {case.title}")
        lines.append(f"category: {case.category}")
        lines.append(f"severity: {case.severity}")
        lines.append(f"created_at: {case.created_at.isoformat()}")
        lines.append(f"updated_at: {case.updated_at.isoformat()}")
        lines.append(f"tags: {case.tags}")
        if case.cluster:
            lines.append(f"cluster: {case.cluster}")
        if case.service:
            lines.append(f"service: {case.service}")
        if case.related_cases:
            lines.append(f"related_cases: {case.related_cases}")
        lines.append("---")
        lines.append("")
        
        if case.problem:
            lines.append("## 问题现象")
            lines.append("")
            lines.append(case.problem)
            lines.append("")
        
        if case.symptoms:
            lines.append("## 症状列表")
            lines.append("")
            for symptom in case.symptoms:
                lines.append(f"- {symptom}")
            lines.append("")
        
        if case.analysis:
            lines.append("## 分析过程")
            lines.append("")
            lines.append(case.analysis)
            lines.append("")
        
        if case.solution:
            lines.append("## 解决方案")
            lines.append("")
            for i, step in enumerate(case.solution, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        
        if case.verification:
            lines.append("## 验证结果")
            lines.append("")
            lines.append(case.verification)
            lines.append("")
        
        if case.references:
            lines.append("## 参考资料")
            lines.append("")
            for ref in case.references:
                lines.append(f"- {ref}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def list_all(
        self,
        category: str | None = None,
        limit: int = 100
    ) -> list[Case]:
        """List all cases."""
        cases = list(self.index.values())
        if category:
            cases = [c for c in cases if c.category == category]
        return sorted(cases, key=lambda c: c.created_at, reverse=True)[:limit]
    
    async def delete(self, case_id: str) -> bool:
        """Delete case."""
        if case_id not in self.index:
            return False
        
        case = self.index[case_id]
        
        title_slug = re.sub(r"[^\w\u4e00-\u9fa5a-z0-9]", "-", case.title.lower())
        title_slug = re.sub(r"-+", "-", title_slug).strip("-")
        file_path = self.case_dir / case.category / f"{case_id}-{title_slug}.md"
        
        if file_path.exists():
            file_path.unlink()
        
        del self.index[case_id]
        return True
    
    async def reload(self) -> None:
        """Reload all cases."""
        self.index.clear()
        self._load_index()