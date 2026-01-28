"""
Tests for the GeminiClient module.

Tests prompt generation, JSON parsing, PRD validation, and fallback behavior.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from modules.gemini_client import GeminiClient


@pytest.fixture
def client():
    """Create a GeminiClient with no API key (unconfigured)."""
    with patch.dict('os.environ', {}, clear=False):
        c = GeminiClient(api_key=None)
        c.configured = False
        return c


@pytest.fixture
def configured_client(mock_gemini_model):
    """Create a GeminiClient with a mocked model."""
    with patch.dict('os.environ', {}, clear=False):
        c = GeminiClient(api_key=None)
        c.configured = True
        c.model = mock_gemini_model
        return c


class TestEnhanceIdea:
    def test_empty_idea_raises(self, client):
        with pytest.raises(ValueError, match="cannot be empty"):
            client.enhance_idea("")

    def test_none_idea_raises(self, client):
        with pytest.raises(ValueError, match="cannot be empty"):
            client.enhance_idea(None)

    def test_fallback_returns_structured_dict(self, client, sample_app_idea):
        result = client.enhance_idea(sample_app_idea)
        assert "title" in result
        assert "description" in result
        assert "target_users" in result
        assert "problem_statement" in result
        assert "key_value_props" in result
        assert "suggested_tech_stack" in result
        assert isinstance(result["key_value_props"], list)
        assert isinstance(result["suggested_tech_stack"], dict)

    def test_fallback_with_tech_prefs(self, client, sample_app_idea):
        result = client.enhance_idea(sample_app_idea, tech_preferences="Use Rust and React")
        assert result["suggested_tech_stack"].get("notes") == "Use Rust and React"

    def test_configured_client_uses_model(self, configured_client, sample_app_idea, sample_enhanced_idea):
        configured_client.model.generate_content.return_value = MagicMock(
            text=json.dumps(sample_enhanced_idea)
        )
        result = configured_client.enhance_idea(sample_app_idea)
        assert result["title"] == "TeamFlow"
        configured_client.model.generate_content.assert_called_once()

    def test_configured_client_falls_back_on_error(self, configured_client, sample_app_idea):
        configured_client.model.generate_content.side_effect = Exception("API error")
        result = configured_client.enhance_idea(sample_app_idea)
        # Should still return a valid structure
        assert "title" in result
        assert "description" in result


class TestGeneratePRD:
    def test_missing_title_raises(self, client):
        with pytest.raises(ValueError, match="must have a title"):
            client.generate_prd({})

    def test_fallback_prd_has_epics(self, client, sample_enhanced_idea):
        result = client.generate_prd(sample_enhanced_idea)
        assert "prd" in result
        assert "prd_markdown" in result
        prd = result["prd"]
        assert len(prd["epics"]) >= 3
        # Check that fallback is domain-aware (mentions user/auth since description has "team")
        epic_names = [e["name"] for e in prd["epics"]]
        assert any("Setup" in n or "Infrastructure" in n for n in epic_names)

    def test_fallback_prd_has_architecture(self, client, sample_enhanced_idea):
        result = client.generate_prd(sample_enhanced_idea)
        arch = result["prd"]["technical_architecture"]
        assert arch.get("overview")
        assert len(arch.get("components", [])) > 0

    def test_fallback_prd_has_nfrs(self, client, sample_enhanced_idea):
        result = client.generate_prd(sample_enhanced_idea)
        nfr = result["prd"]["non_functional_requirements"]
        assert "performance" in nfr
        assert "security" in nfr
        assert "error_handling" in nfr

    def test_configured_client_generates_prd(self, configured_client, sample_enhanced_idea, sample_prd):
        configured_client.model.generate_content.return_value = MagicMock(
            text=json.dumps(sample_prd)
        )
        result = configured_client.generate_prd(sample_enhanced_idea)
        assert result["prd"]["epics"][0]["name"] == "Project Setup & Infrastructure"


class TestParseJsonResponse:
    def test_parse_direct_json(self, client):
        result = client._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_markdown_fenced(self, client):
        text = '```json\n{"key": "value"}\n```'
        result = client._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_json_in_text(self, client):
        text = 'Here is the result: {"key": "value"} and more text'
        result = client._parse_json_response(text)
        assert result == {"key": "value"}

    def test_parse_invalid_returns_none(self, client):
        result = client._parse_json_response("not json at all")
        assert result is None


class TestPRDValidation:
    def test_find_issues_too_few_epics(self, client):
        prd = {"epics": [{"name": "Only One", "user_stories": []}]}
        issues = client._find_prd_issues(prd)
        assert "too_few_epics" in issues

    def test_find_issues_vague_features(self, client):
        prd = {
            "epics": [{
                "name": "Epic 1", "priority": "P0",
                "user_stories": [{
                    "title": "Story",
                    "acceptance_criteria": ["AC1", "AC2"],
                    "features": [
                        {"name": "F1", "description": "short"},
                        {"name": "F2", "description": "also short"},
                        {"name": "F3", "description": "too short too"}
                    ]
                }]
            }, {"name": "E2", "priority": "P1", "user_stories": []},
               {"name": "E3", "priority": "P2", "user_stories": []}]
        }
        issues = client._find_prd_issues(prd)
        assert "vague_feature_descriptions" in issues

    def test_find_issues_missing_data_model(self, client):
        prd = {
            "epics": [
                {"name": "E1", "user_stories": []},
                {"name": "E2", "user_stories": []},
                {"name": "E3", "user_stories": []}
            ],
            "technical_architecture": {"data_model": [], "api_endpoints": []}
        }
        issues = client._find_prd_issues(prd)
        assert "missing_data_model" in issues
        assert "missing_api_endpoints" in issues

    def test_structural_fixes_add_depends_on(self, client, sample_prd):
        # Remove depends_on to test fix
        for epic in sample_prd["epics"]:
            if "depends_on" in epic:
                del epic["depends_on"]
        fixed = client._apply_structural_fixes(sample_prd)
        # First epic should have empty depends_on, others should depend on first
        assert fixed["epics"][0].get("depends_on") == []
        assert len(fixed["epics"][1].get("depends_on", [])) > 0

    def test_structural_fixes_add_error_handling(self, client):
        prd = {
            "epics": [{"name": "E1", "user_stories": []}],
            "non_functional_requirements": {"performance": ["fast"]}
        }
        fixed = client._apply_structural_fixes(prd)
        assert "error_handling" in fixed["non_functional_requirements"]


class TestMarkdownGeneration:
    def test_markdown_includes_title(self, client, sample_prd, sample_enhanced_idea):
        md = client._prd_to_markdown(sample_prd, sample_enhanced_idea)
        assert "TeamFlow" in md

    def test_markdown_includes_epics(self, client, sample_prd, sample_enhanced_idea):
        md = client._prd_to_markdown(sample_prd, sample_enhanced_idea)
        assert "Project Setup & Infrastructure" in md
        assert "Authentication" in md

    def test_markdown_includes_dependencies(self, client, sample_prd, sample_enhanced_idea):
        md = client._prd_to_markdown(sample_prd, sample_enhanced_idea)
        assert "Depends on:" in md
