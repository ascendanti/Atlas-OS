"""
Tests for the GitHub Repository Analyzer (KNOW-005)
"""

import pytest
from unittest.mock import patch, MagicMock

from modules.knowledge.repo_analyzer import RepoAnalyzer


@pytest.fixture
def analyzer(tmp_path):
    """Create a RepoAnalyzer with test database."""
    from modules.core.database import Database
    from modules.core.event_store import EventStore

    db = Database(str(tmp_path / "test.db"))
    event_store = EventStore(db)
    return RepoAnalyzer(event_store=event_store)


@pytest.fixture
def mock_github_responses():
    """Mock GitHub API responses."""
    repo_info = {
        "name": "test-repo",
        "description": "A test repository",
        "stargazers_count": 1500,
        "forks_count": 200,
        "language": "Python",
        "topics": ["python", "automation", "testing"],
        "default_branch": "main",
    }

    tree = {
        "tree": [
            {"path": "src", "type": "tree"},
            {"path": "tests", "type": "tree"},
            {"path": "modules", "type": "tree"},
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/utils.py", "type": "blob"},
            {"path": "requirements.txt", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "setup.py", "type": "blob"},
            {"path": "pytest.ini", "type": "blob"},
            {"path": ".github/workflows/test.yml", "type": "blob"},
        ]
    }

    return repo_info, tree


class TestRepoAnalyzer:
    """Tests for RepoAnalyzer class."""

    def test_parse_github_url(self, analyzer):
        """Test parsing various GitHub URL formats."""
        # Standard URL
        owner, repo = analyzer._parse_github_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

        # URL with trailing slash
        owner, repo = analyzer._parse_github_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo == "repo"

        # URL with .git suffix
        owner, repo = analyzer._parse_github_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_github_url(self, analyzer):
        """Test parsing invalid GitHub URLs."""
        with pytest.raises(ValueError):
            analyzer._parse_github_url("https://github.com/owner")

    @patch("requests.get")
    def test_analyze_repository(self, mock_get, analyzer, mock_github_responses):
        """Test analyzing a repository."""
        repo_info, tree = mock_github_responses

        # Mock API responses
        mock_response_repo = MagicMock()
        mock_response_repo.json.return_value = repo_info
        mock_response_repo.status_code = 200
        mock_response_repo.raise_for_status = MagicMock()

        mock_response_tree = MagicMock()
        mock_response_tree.json.return_value = tree
        mock_response_tree.status_code = 200
        mock_response_tree.raise_for_status = MagicMock()

        mock_response_readme = MagicMock()
        mock_response_readme.json.return_value = {
            "content": "IyBUZXN0IFJlcG8=",  # "# Test Repo" base64 encoded
            "encoding": "base64"
        }
        mock_response_readme.status_code = 200

        mock_response_reqs = MagicMock()
        mock_response_reqs.json.return_value = {
            "content": "Zmxhc2sKcHl0ZXN0",  # "flask\npytest" base64 encoded
            "encoding": "base64"
        }
        mock_response_reqs.status_code = 200

        def mock_get_impl(url, *args, **kwargs):
            if "/repos/owner/test-repo" in url and "/git/trees" not in url and "/contents" not in url:
                return mock_response_repo
            elif "/git/trees" in url:
                return mock_response_tree
            elif "README.md" in url:
                return mock_response_readme
            elif "requirements.txt" in url:
                return mock_response_reqs
            else:
                mock_404 = MagicMock()
                mock_404.status_code = 404
                return mock_404

        mock_get.side_effect = mock_get_impl

        # Analyze
        analysis_id = analyzer.analyze(
            "https://github.com/owner/test-repo",
            notes="Testing the analyzer",
            tags=["test", "python"]
        )

        assert analysis_id == 1

        # Verify analysis
        analysis = analyzer.get(analysis_id)
        assert analysis is not None
        assert analysis["repo_name"] == "test-repo"
        assert analysis["language"] == "Python"
        assert analysis["stars"] == 1500
        assert analysis["notes"] == "Testing the analyzer"
        assert "test" in analysis["tags"]

    def test_add_lesson(self, analyzer):
        """Test adding a lesson to an analysis."""
        # Create a mock analysis first (using direct event emission)
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/repo",
                "owner": "test",
                "repo_name": "repo",
                "description": "Test",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": [],
                "structure": {},
                "technologies": {},
                "patterns": [],
                "readme_preview": "",
                "notes": "",
                "tags": [],
            }
        )
        analyzer._next_id = 2

        # Add lesson
        result = analyzer.add_lesson(
            1,
            "Use event sourcing",
            "Event sourcing provides audit trail",
            "Atlas-OS architecture"
        )
        assert result is True

        # Verify
        analysis = analyzer.get(1)
        assert len(analysis["lessons"]) == 1
        assert analysis["lessons"][0]["title"] == "Use event sourcing"

    def test_add_pattern(self, analyzer):
        """Test adding a pattern to an analysis."""
        # Create a mock analysis
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/repo",
                "owner": "test",
                "repo_name": "repo",
                "description": "Test",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": [],
                "structure": {},
                "technologies": {},
                "patterns": [],
                "readme_preview": "",
                "notes": "",
                "tags": [],
            }
        )
        analyzer._next_id = 2

        # Add pattern
        result = analyzer.add_pattern(
            1,
            "Repository Pattern",
            "Abstracts data access",
            "Database operations"
        )
        assert result is True

        # Verify
        analysis = analyzer.get(1)
        assert len(analysis["manual_patterns"]) == 1
        assert analysis["manual_patterns"][0]["pattern_name"] == "Repository Pattern"

    def test_list_analyses(self, analyzer):
        """Test listing analyses."""
        # Create two analyses
        for i in range(2):
            analyzer.event_store.emit(
                event_type="REPO_ANALYZED",
                entity_type=analyzer.ENTITY_TYPE,
                entity_id=i + 1,
                payload={
                    "github_url": f"https://github.com/test/repo{i+1}",
                    "owner": "test",
                    "repo_name": f"repo{i+1}",
                    "description": f"Test {i+1}",
                    "stars": 100 * (i + 1),
                    "forks": 10,
                    "language": "Python" if i == 0 else "JavaScript",
                    "topics": [],
                    "structure": {},
                    "technologies": {},
                    "patterns": [],
                    "readme_preview": "",
                    "notes": "",
                    "tags": ["test"] if i == 0 else ["js"],
                }
            )
        analyzer._next_id = 3

        # List all
        analyses = analyzer.list_analyses()
        assert len(analyses) == 2

        # Filter by language
        py_analyses = analyzer.list_analyses(language="Python")
        assert len(py_analyses) == 1
        assert py_analyses[0]["repo_name"] == "repo1"

        # Filter by tag
        tagged = analyzer.list_analyses(tag="test")
        assert len(tagged) == 1

    def test_archive(self, analyzer):
        """Test archiving an analysis."""
        # Create analysis
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/repo",
                "owner": "test",
                "repo_name": "repo",
                "description": "Test",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": [],
                "structure": {},
                "technologies": {},
                "patterns": [],
                "readme_preview": "",
                "notes": "",
                "tags": [],
            }
        )
        analyzer._next_id = 2

        # Archive
        result = analyzer.archive(1)
        assert result is True

        # Verify
        analysis = analyzer.get(1)
        assert analysis["archived"] is True

        # Should not appear in default list
        analyses = analyzer.list_analyses()
        assert len(analyses) == 0

        # But should appear with include_archived
        analyses = analyzer.list_analyses(include_archived=True)
        assert len(analyses) == 1

    def test_generate_report(self, analyzer):
        """Test generating a markdown report."""
        # Create analysis
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/awesome-repo",
                "owner": "test",
                "repo_name": "awesome-repo",
                "description": "An awesome repository for testing",
                "stars": 5000,
                "forks": 500,
                "language": "Python",
                "topics": ["python", "testing"],
                "structure": {"top_level_dirs": ["src", "tests"], "total_files": 50},
                "technologies": {"languages": ["Python"], "frameworks": ["FastAPI"], "tools": ["pytest"]},
                "patterns": [{"name": "API Layer", "confidence": "high", "evidence": "api directory"}],
                "readme_preview": "# Awesome Repo",
                "notes": "",
                "tags": ["reference"],
            }
        )
        analyzer._next_id = 2

        # Generate report
        report = analyzer.generate_report(1)
        assert "# Repository Analysis: awesome-repo" in report
        assert "**Stars:** 5,000" in report
        assert "Python" in report
        assert "FastAPI" in report
        assert "API Layer" in report

    def test_get_all_patterns(self, analyzer):
        """Test getting all patterns across repos."""
        # Create analysis with patterns
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/repo",
                "owner": "test",
                "repo_name": "repo",
                "description": "Test",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": [],
                "structure": {},
                "technologies": {},
                "patterns": [
                    {"name": "MVC", "confidence": "high", "evidence": "directories"}
                ],
                "readme_preview": "",
                "notes": "",
                "tags": [],
            }
        )
        analyzer._next_id = 2

        # Add manual pattern
        analyzer.add_pattern(1, "Singleton", "Single instance", "Global state")

        # Get all patterns
        patterns = analyzer.get_all_patterns()
        assert len(patterns) == 2
        pattern_names = [p.get("name", p.get("pattern_name")) for p in patterns]
        assert "MVC" in pattern_names
        assert "Singleton" in pattern_names

    def test_explain(self, analyzer):
        """Test explain functionality."""
        # Create analysis and add events
        analyzer.event_store.emit(
            event_type="REPO_ANALYZED",
            entity_type=analyzer.ENTITY_TYPE,
            entity_id=1,
            payload={
                "github_url": "https://github.com/test/repo",
                "owner": "test",
                "repo_name": "repo",
                "description": "Test",
                "stars": 100,
                "forks": 10,
                "language": "Python",
                "topics": [],
                "structure": {},
                "technologies": {},
                "patterns": [],
                "readme_preview": "",
                "notes": "",
                "tags": [],
            }
        )
        analyzer._next_id = 2

        analyzer.add_lesson(1, "Lesson 1", "Description", "Apply here")

        # Get events
        events = analyzer.explain(1)
        assert len(events) == 2
        assert events[0]["event_type"] == "REPO_ANALYZED"
        assert events[1]["event_type"] == "LESSON_LEARNED"


class TestStructureAnalysis:
    """Tests for structure analysis functionality."""

    def test_analyze_structure(self, analyzer):
        """Test structure analysis."""
        tree = [
            {"path": "src", "type": "tree"},
            {"path": "tests", "type": "tree"},
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/utils.py", "type": "blob"},
            {"path": "tests/test_main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]

        result = analyzer._analyze_structure(tree)

        assert "src" in result["top_level_dirs"]
        assert "tests" in result["top_level_dirs"]
        assert result["total_files"] == 4
        assert ".py" in result["files_by_extension"]
        assert ".md" in result["files_by_extension"]


class TestTechnologyDetection:
    """Tests for technology detection."""

    @patch("requests.get")
    def test_detect_python(self, mock_get, analyzer):
        """Test Python detection."""
        tree = [
            {"path": "main.py", "type": "blob"},
            {"path": "requirements.txt", "type": "blob"},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = analyzer._detect_technologies(tree, "owner", "repo")
        assert "Python" in result["languages"]

    @patch("requests.get")
    def test_detect_javascript(self, mock_get, analyzer):
        """Test JavaScript detection."""
        tree = [
            {"path": "index.js", "type": "blob"},
            {"path": "package.json", "type": "blob"},
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "eyJuYW1lIjoidGVzdCIsImRlcGVuZGVuY2llcyI6eyJyZWFjdCI6Il4xOC4wLjAifX0=",  # package.json with react
            "encoding": "base64"
        }
        mock_get.return_value = mock_response

        result = analyzer._detect_technologies(tree, "owner", "repo")
        assert "JavaScript" in result["languages"]
        assert "React" in result["frameworks"]


class TestPatternDetection:
    """Tests for pattern detection."""

    def test_detect_modular_pattern(self, analyzer):
        """Test modular architecture detection."""
        tree = [
            {"path": "modules", "type": "tree"},
            {"path": "modules/core", "type": "tree"},
            {"path": "modules/api", "type": "tree"},
        ]

        patterns = analyzer._identify_patterns(tree, "owner", "repo")
        pattern_names = [p["name"] for p in patterns]
        assert "Modular Architecture" in pattern_names

    def test_detect_test_suite(self, analyzer):
        """Test test suite detection."""
        tree = [
            {"path": "tests", "type": "tree"},
            {"path": "tests/test_main.py", "type": "blob"},
        ]

        patterns = analyzer._identify_patterns(tree, "owner", "repo")
        pattern_names = [p["name"] for p in patterns]
        assert "Test Suite" in pattern_names

    def test_detect_api_layer(self, analyzer):
        """Test API layer detection."""
        tree = [
            {"path": "api", "type": "tree"},
            {"path": "api/routes.py", "type": "blob"},
        ]

        patterns = analyzer._identify_patterns(tree, "owner", "repo")
        pattern_names = [p["name"] for p in patterns]
        assert "API Layer" in pattern_names
