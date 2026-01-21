"""
Atlas Personal OS - GitHub Repository Analyzer (KNOW-005)

Onboarding function for analyzing external GitHub repositories:
- Fetch repository structure and metadata via GitHub API
- Analyze architecture patterns and technologies
- Document findings and lessons learned
- Store analysis for future reference
"""

from __future__ import annotations
import os
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from modules.core.event_store import EventStore, get_event_store


# Event Types
REPO_ANALYZED = "REPO_ANALYZED"
REPO_UPDATED = "REPO_UPDATED"
PATTERN_IDENTIFIED = "PATTERN_IDENTIFIED"
LESSON_LEARNED = "LESSON_LEARNED"
REPO_ARCHIVED = "REPO_ARCHIVED"


class RepoAnalyzer:
    """
    Event-sourced GitHub repository analyzer.

    Analyzes external repositories to learn patterns,
    architecture decisions, and best practices.
    """

    ENTITY_TYPE = "github_repo"

    def __init__(self, event_store: Optional[EventStore] = None):
        self.event_store = event_store or get_event_store()
        self._next_id = self._compute_next_id()
        self._github_token = os.getenv("GITHUB_TOKEN", "")

    def _compute_next_id(self) -> int:
        """Compute next repo ID from events."""
        events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=REPO_ANALYZED
        )
        if not events:
            return 1
        return max(int(e["entity_id"]) for e in events) + 1

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Parse owner and repo name from GitHub URL."""
        # Handle various GitHub URL formats
        url = url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]

        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = path.split("/")

        if len(parts) >= 2:
            return parts[0], parts[1]
        raise ValueError(f"Invalid GitHub URL: {url}")

    def _get_headers(self) -> dict:
        """Get HTTP headers for GitHub API."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self._github_token:
            headers["Authorization"] = f"token {self._github_token}"
        return headers

    def _fetch_repo_info(self, owner: str, repo: str) -> dict:
        """Fetch repository metadata from GitHub API."""
        import requests

        url = f"https://api.github.com/repos/{owner}/{repo}"
        resp = requests.get(url, headers=self._get_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _fetch_repo_tree(self, owner: str, repo: str, branch: str = "main") -> List[dict]:
        """Fetch repository file tree."""
        import requests

        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = requests.get(url, headers=self._get_headers(), timeout=30)

        if resp.status_code == 404:
            # Try master branch
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
            resp = requests.get(url, headers=self._get_headers(), timeout=30)

        resp.raise_for_status()
        return resp.json().get("tree", [])

    def _fetch_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch content of a specific file."""
        import requests
        import base64

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        resp = requests.get(url, headers=self._get_headers(), timeout=30)

        if resp.status_code != 200:
            return ""

        data = resp.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
        return data.get("content", "")

    def _analyze_structure(self, tree: List[dict]) -> dict:
        """Analyze repository directory structure."""
        dirs = set()
        files_by_type = {}
        total_files = 0

        for item in tree:
            if item.get("type") == "tree":
                dirs.add(item["path"].split("/")[0])
            elif item.get("type") == "blob":
                total_files += 1
                ext = os.path.splitext(item["path"])[1].lower()
                files_by_type[ext] = files_by_type.get(ext, 0) + 1

        return {
            "top_level_dirs": sorted(dirs),
            "files_by_extension": dict(sorted(
                files_by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )[:15]),
            "total_files": total_files,
        }

    def _detect_technologies(self, tree: List[dict], owner: str, repo: str) -> dict:
        """Detect technologies and frameworks used."""
        tech = {
            "languages": [],
            "frameworks": [],
            "tools": [],
            "databases": [],
        }

        file_paths = [item["path"] for item in tree if item.get("type") == "blob"]

        # Language detection by files
        lang_indicators = {
            "Python": [".py", "requirements.txt", "setup.py", "pyproject.toml"],
            "JavaScript": [".js", "package.json"],
            "TypeScript": [".ts", ".tsx", "tsconfig.json"],
            "Go": [".go", "go.mod"],
            "Rust": [".rs", "Cargo.toml"],
            "Java": [".java", "pom.xml", "build.gradle"],
            "Ruby": [".rb", "Gemfile"],
            "PHP": [".php", "composer.json"],
        }

        for lang, indicators in lang_indicators.items():
            if any(any(f.endswith(ind) for f in file_paths) for ind in indicators):
                tech["languages"].append(lang)

        # Framework detection
        framework_files = {
            "React": ["package.json"],  # Will check content
            "Vue": ["vue.config.js", "nuxt.config.js"],
            "Django": ["manage.py", "django"],
            "Flask": ["flask"],
            "FastAPI": ["fastapi"],
            "Express": ["express"],
            "Rails": ["config/routes.rb"],
            "Spring": ["spring"],
        }

        # Check package.json for JS frameworks
        if "package.json" in file_paths:
            try:
                pkg = self._fetch_file_content(owner, repo, "package.json")
                if "react" in pkg.lower():
                    tech["frameworks"].append("React")
                if "vue" in pkg.lower():
                    tech["frameworks"].append("Vue")
                if "angular" in pkg.lower():
                    tech["frameworks"].append("Angular")
                if "next" in pkg.lower():
                    tech["frameworks"].append("Next.js")
                if "express" in pkg.lower():
                    tech["frameworks"].append("Express")
            except Exception:
                pass

        # Check requirements.txt for Python frameworks
        if "requirements.txt" in file_paths:
            try:
                reqs = self._fetch_file_content(owner, repo, "requirements.txt")
                if "django" in reqs.lower():
                    tech["frameworks"].append("Django")
                if "flask" in reqs.lower():
                    tech["frameworks"].append("Flask")
                if "fastapi" in reqs.lower():
                    tech["frameworks"].append("FastAPI")
            except Exception:
                pass

        # Tool detection
        if "Dockerfile" in file_paths or "docker-compose.yml" in file_paths:
            tech["tools"].append("Docker")
        if ".github/workflows" in str(file_paths):
            tech["tools"].append("GitHub Actions")
        if "Makefile" in file_paths:
            tech["tools"].append("Make")
        if "pytest.ini" in file_paths or "conftest.py" in file_paths:
            tech["tools"].append("pytest")
        if "jest.config" in str(file_paths):
            tech["tools"].append("Jest")

        return tech

    def _identify_patterns(self, tree: List[dict], owner: str, repo: str) -> List[dict]:
        """Identify architectural patterns."""
        patterns = []
        file_paths = [item["path"] for item in tree if item.get("type") == "blob"]
        dir_paths = [item["path"] for item in tree if item.get("type") == "tree"]

        # Event sourcing
        if any("event" in f.lower() for f in file_paths):
            patterns.append({
                "name": "Event Sourcing",
                "confidence": "medium",
                "evidence": "Event-related files found",
            })

        # MVC/Modular
        if any(d in ["models", "views", "controllers"] for d in dir_paths):
            patterns.append({
                "name": "MVC Architecture",
                "confidence": "high",
                "evidence": "models/views/controllers directories",
            })

        if "modules" in dir_paths or "src/modules" in dir_paths:
            patterns.append({
                "name": "Modular Architecture",
                "confidence": "high",
                "evidence": "modules directory structure",
            })

        # API patterns
        if any("api" in f.lower() for f in dir_paths):
            patterns.append({
                "name": "API Layer",
                "confidence": "high",
                "evidence": "api directory found",
            })

        # Test patterns
        if "tests" in dir_paths or "test" in dir_paths:
            patterns.append({
                "name": "Test Suite",
                "confidence": "high",
                "evidence": "tests directory found",
            })

        # Configuration patterns
        if any(f.endswith(".env.example") or f == ".env.example" for f in file_paths):
            patterns.append({
                "name": "Environment Configuration",
                "confidence": "high",
                "evidence": ".env.example file",
            })

        return patterns

    # ========================================================================
    # COMMANDS
    # ========================================================================

    def analyze(
        self,
        github_url: str,
        notes: str = "",
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Analyze a GitHub repository.

        Args:
            github_url: Full GitHub repository URL
            notes: Optional notes about why analyzing this repo
            tags: Optional tags for categorization

        Returns:
            Analysis ID
        """
        owner, repo = self._parse_github_url(github_url)

        # Fetch repository data
        repo_info = self._fetch_repo_info(owner, repo)
        tree = self._fetch_repo_tree(owner, repo, repo_info.get("default_branch", "main"))

        # Analyze
        structure = self._analyze_structure(tree)
        technologies = self._detect_technologies(tree, owner, repo)
        patterns = self._identify_patterns(tree, owner, repo)

        # Fetch README if exists
        readme_content = ""
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            readme_content = self._fetch_file_content(owner, repo, readme_name)
            if readme_content:
                break

        analysis_id = self._next_id
        self._next_id += 1

        self.event_store.emit(
            event_type=REPO_ANALYZED,
            entity_type=self.ENTITY_TYPE,
            entity_id=analysis_id,
            payload={
                "github_url": github_url,
                "owner": owner,
                "repo_name": repo,
                "description": repo_info.get("description", ""),
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
                "language": repo_info.get("language", ""),
                "topics": repo_info.get("topics", []),
                "structure": structure,
                "technologies": technologies,
                "patterns": patterns,
                "readme_preview": readme_content[:2000] if readme_content else "",
                "notes": notes,
                "tags": tags or [],
            }
        )

        return analysis_id

    def add_pattern(
        self,
        analysis_id: int,
        pattern_name: str,
        description: str,
        applicability: str = "",
        code_example: str = "",
    ) -> bool:
        """Add a manually identified pattern."""
        analysis = self.get(analysis_id)
        if not analysis:
            return False

        self.event_store.emit(
            event_type=PATTERN_IDENTIFIED,
            entity_type=self.ENTITY_TYPE,
            entity_id=analysis_id,
            payload={
                "pattern_name": pattern_name,
                "description": description,
                "applicability": applicability,
                "code_example": code_example,
            }
        )
        return True

    def add_lesson(
        self,
        analysis_id: int,
        title: str,
        description: str,
        apply_to: str = "",
    ) -> bool:
        """Record a lesson learned from the repo."""
        analysis = self.get(analysis_id)
        if not analysis:
            return False

        self.event_store.emit(
            event_type=LESSON_LEARNED,
            entity_type=self.ENTITY_TYPE,
            entity_id=analysis_id,
            payload={
                "title": title,
                "description": description,
                "apply_to": apply_to,
                "learned_at": datetime.now().isoformat(),
            }
        )
        return True

    def archive(self, analysis_id: int) -> bool:
        """Archive an analysis."""
        analysis = self.get(analysis_id)
        if not analysis:
            return False

        self.event_store.emit(
            event_type=REPO_ARCHIVED,
            entity_type=self.ENTITY_TYPE,
            entity_id=analysis_id,
            payload={"archived": True}
        )
        return True

    # ========================================================================
    # PROJECTIONS
    # ========================================================================

    def get(self, analysis_id: int) -> Optional[dict]:
        """Get analysis by projecting from events."""
        events = self.event_store.explain(self.ENTITY_TYPE, analysis_id)
        if not events:
            return None
        return self._project(analysis_id, events)

    def _project(self, analysis_id: int, events: list[dict]) -> dict:
        """Project state from events."""
        state = {
            "id": analysis_id,
            "github_url": "",
            "owner": "",
            "repo_name": "",
            "description": "",
            "stars": 0,
            "forks": 0,
            "language": "",
            "topics": [],
            "structure": {},
            "technologies": {},
            "patterns": [],
            "manual_patterns": [],
            "lessons": [],
            "readme_preview": "",
            "notes": "",
            "tags": [],
            "analyzed_at": None,
            "archived": False,
        }

        for event in events:
            payload = event["payload"]
            timestamp = event["timestamp"]

            if event["event_type"] == REPO_ANALYZED:
                state.update({
                    "github_url": payload.get("github_url", ""),
                    "owner": payload.get("owner", ""),
                    "repo_name": payload.get("repo_name", ""),
                    "description": payload.get("description", ""),
                    "stars": payload.get("stars", 0),
                    "forks": payload.get("forks", 0),
                    "language": payload.get("language", ""),
                    "topics": payload.get("topics", []),
                    "structure": payload.get("structure", {}),
                    "technologies": payload.get("technologies", {}),
                    "patterns": payload.get("patterns", []),
                    "readme_preview": payload.get("readme_preview", ""),
                    "notes": payload.get("notes", ""),
                    "tags": payload.get("tags", []),
                    "analyzed_at": timestamp,
                })

            elif event["event_type"] == PATTERN_IDENTIFIED:
                state["manual_patterns"].append({
                    "pattern_name": payload.get("pattern_name", ""),
                    "description": payload.get("description", ""),
                    "applicability": payload.get("applicability", ""),
                    "code_example": payload.get("code_example", ""),
                })

            elif event["event_type"] == LESSON_LEARNED:
                state["lessons"].append({
                    "title": payload.get("title", ""),
                    "description": payload.get("description", ""),
                    "apply_to": payload.get("apply_to", ""),
                    "learned_at": payload.get("learned_at"),
                })

            elif event["event_type"] == REPO_ARCHIVED:
                state["archived"] = True

        return state

    def list_analyses(
        self,
        tag: Optional[str] = None,
        language: Optional[str] = None,
        include_archived: bool = False,
        limit: int = 100,
    ) -> List[dict]:
        """List all analyses with optional filters."""
        created_events = self.event_store.query(
            entity_type=self.ENTITY_TYPE,
            event_type=REPO_ANALYZED,
            limit=1000
        )

        analyses = []
        for event in created_events:
            aid = int(event["entity_id"])
            analysis = self.get(aid)
            if analysis:
                if not include_archived and analysis["archived"]:
                    continue
                if tag and tag not in analysis["tags"]:
                    continue
                if language and analysis["language"].lower() != language.lower():
                    continue
                analyses.append(analysis)

        return analyses[:limit]

    def get_all_patterns(self) -> List[dict]:
        """Get all identified patterns across all repos."""
        analyses = self.list_analyses(include_archived=True, limit=1000)
        all_patterns = []

        for analysis in analyses:
            for pattern in analysis.get("patterns", []):
                pattern["source_repo"] = analysis["github_url"]
                all_patterns.append(pattern)
            for pattern in analysis.get("manual_patterns", []):
                pattern["source_repo"] = analysis["github_url"]
                all_patterns.append(pattern)

        return all_patterns

    def get_all_lessons(self) -> List[dict]:
        """Get all lessons learned across all repos."""
        analyses = self.list_analyses(include_archived=True, limit=1000)
        all_lessons = []

        for analysis in analyses:
            for lesson in analysis.get("lessons", []):
                lesson["source_repo"] = analysis["github_url"]
                all_lessons.append(lesson)

        return all_lessons

    def generate_report(self, analysis_id: int) -> str:
        """Generate a markdown report for an analysis."""
        analysis = self.get(analysis_id)
        if not analysis:
            return ""

        lines = [
            f"# Repository Analysis: {analysis['repo_name']}",
            "",
            f"**URL:** {analysis['github_url']}",
            f"**Analyzed:** {analysis['analyzed_at']}",
            f"**Primary Language:** {analysis['language']}",
            f"**Stars:** {analysis['stars']:,} | **Forks:** {analysis['forks']:,}",
            "",
            "## Description",
            analysis['description'] or "_No description_",
            "",
            "## Technologies Detected",
            "",
        ]

        tech = analysis.get("technologies", {})
        if tech.get("languages"):
            lines.append(f"**Languages:** {', '.join(tech['languages'])}")
        if tech.get("frameworks"):
            lines.append(f"**Frameworks:** {', '.join(tech['frameworks'])}")
        if tech.get("tools"):
            lines.append(f"**Tools:** {', '.join(tech['tools'])}")

        lines.extend(["", "## Structure", ""])
        struct = analysis.get("structure", {})
        if struct.get("top_level_dirs"):
            lines.append(f"**Top-level directories:** {', '.join(struct['top_level_dirs'])}")
        lines.append(f"**Total files:** {struct.get('total_files', 0)}")

        lines.extend(["", "## Architectural Patterns", ""])
        for pattern in analysis.get("patterns", []):
            lines.append(f"- **{pattern['name']}** ({pattern['confidence']} confidence)")
            lines.append(f"  - Evidence: {pattern['evidence']}")

        if analysis.get("manual_patterns"):
            lines.extend(["", "### Manually Identified Patterns", ""])
            for pattern in analysis["manual_patterns"]:
                lines.append(f"- **{pattern['pattern_name']}**: {pattern['description']}")

        if analysis.get("lessons"):
            lines.extend(["", "## Lessons Learned", ""])
            for lesson in analysis["lessons"]:
                lines.append(f"### {lesson['title']}")
                lines.append(lesson['description'])
                if lesson.get("apply_to"):
                    lines.append(f"_Apply to: {lesson['apply_to']}_")
                lines.append("")

        return "\n".join(lines)

    def explain(self, analysis_id: int) -> List[dict]:
        """Get event history for an analysis."""
        return self.event_store.explain(self.ENTITY_TYPE, analysis_id)
